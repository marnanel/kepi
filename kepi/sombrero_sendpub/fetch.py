# fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

import requests
import django.db.utils
from django.conf import settings
from urllib.parse import urlparse
from kepi.trilby_api.models import RemotePerson
from kepi.sombrero_sendpub.webfinger import get_webfinger

def fetch(address,
        expected_type = None,
        expected_type_for_remote = None,
        expected_type_for_local = None):

    wanted = _parse_address(address)

    wanted['type'] = expected_type

    if wanted['is_local']:
        if expected_type_for_local is not None:
            wanted['type'] = expected_type_for_local

        handler = _fetch_local

    else:
        if expected_type_for_remote is not None:
            wanted['type'] = expected_type_for_remote

        handler = _fetch_remote

    if wanted['type'] is None:
        raise ValueError(
                "fetch() requires some sort of type to be specified")

    return handler(address, wanted)

def _parse_address(address):

    result = {
        'is_atstyle': '@' in address,
    }

    if result['is_atstyle']:
        fields = address.split('@')
        result['username'] = fields[-2]
        result['hostname'] = fields[-1]
    else:
        result['hostname'] = urlparse(address).netloc

    result['is_local'] = result['hostname'] in settings.ALLOWED_HOSTS

    logger.debug("%s: wanted: %s", address, result)

    return result

def _fetch_local(address, wanted):
    raise ValueError("Not yet implemented") # FIXME

def _fetch_remote(address, wanted):

    # Do we already know about them?

    if wanted['is_atstyle']:
        # XXX Not certain about this (or indeed the benefit
        # of storing "acct" in the Person object). Shouldn't we ask
        # the webfinger module whether it knows them?
        kwargs = {"acct": address}
    else:
        kwargs = {"url": address}

    try:
        result = wanted['type'].objects.get(
                **kwargs,
                )

        logger.debug("%s: already known: %s",
                address, result)

        return result

    except wanted['type'].DoesNotExist:
        pass

    # No, so create them (but don't save yet).

    result = wanted['type'](
            **kwargs,
            )

    if wanted['is_atstyle']:

        webfinger = get_webfinger(
                username = wanted['username'],
                hostname = wanted['hostname'],
                )

        if webfinger.url is None:
            logger.info("%s: webfinger lookup failed; bailing",
                    address)
            result.save()
            return None

        logger.info("%s: webfinger gave us %s",
                address, webfinger.url)
        address = webfinger.url

        result.url = address

    # okay, time to go looking online

    try:
        response = requests.get(
                address,
                headers = {
                    'Accept': 'application/activity+json',
                    },
                )
    except requests.ConnectionError:

        logger.info("%s: can't reach host",
            address)

        if result is not None:
            result.status = 0
            result.save()

        return result

    except requests.TimeoutError:

        logger.info("%s: timeout reaching host",
            address)

        if result is not None:
            result.status = 0
            result.save()

        return result

    # so, we have *something*...

    if result is not None:
        result.status = response.status_code
        result.save()

    if response.status_code!=200:
        # HTTP error; bail immediately
        logger.info("%s: unexpected status code from status lookup: %d",
                address, response.status_code,
                )
        return result

    try:
        found = response.json()
    except ValueError:
        logger.info("%s: response was not JSON; dropping",
                address)

        if result is not None:
            result.status = 0
            result.save()

        return result

    if 'type' not in found:
        logger.info("%s: retrieved JSON did not include a type; dropping",
                address)

        if result is not None:
            result.status = 0
            result.save()

        return result

    if 'id' in found:
        if found['id'] != address:
            logger.info(
                    "%s: user's id was not the source url: got %s; dropping",
                    address, found['id'],
                    )
            result.status = 0
            result.save()

            return result

    # Do we have a handler to finish up with?

    handler_name = 'on_%s' % (
            found['type'].lower(),
            )

    if handler_name in globals():

        try:
            result = globals()[handler_name](found, result)
            logger.info("%s: result was %s",
                    address, result)
        except ValueError as ve:
            logger.info("%s: %s from handler; returning None",
                    address, ve)
            return None

        if not isinstance(result, wanted['type']):

            logger.info("%s:    -- which wasn't %s; returning None",
                    address, wanted['type'])

            return None

        return result

    else:

        # no handler

        logger.info("%s: no %s; returning %s",
                address, handler_name, result)
        return result

def on_person(found, user):

    for foundname, fieldname in [
            ('preferredUsername', 'username'),
            ('name', 'display_name'),
            ('summary', 'note'),
            ('manuallyApprovesFollowers', 'locked'),
            #('following', 'following'),
            #('followers', 'followers'),
            ('inbox', 'inbox'),
            #('outbox', 'outbox'),
            #('featured', 'featured'),
            # ... created_at?
            # ... bot?
            ('movedTo', 'moved_to'),
            ]:
        if foundname in found:
            setattr(user,
                    fieldname,
                    found[foundname])

    # A shared inbox takes priority over a personal inbox
    if 'endpoints' in found:
        if 'sharedInbox' in found['endpoints']:
            user.inbox = found['endpoints']['sharedInbox']

    if 'publicKey' in found:
        key = found['publicKey']

        if 'owner' in key:
            if key['owner'] != user.url:
                raise ValueError(
                        f"Remote user gave us someone else's key ({key['owner']})")

        if 'id' in key:
            user.key_name = key['id']

        if 'publicKeyPem' in key:
            user.publicKey = key['publicKeyPem']

    if user.acct is None:

        # We might already know the acct,
        # if we got to this user by looking up their acct.
        # This will probably have to be cleverer later.

        hostname = urlparse(user.url).netloc
        user.acct = '{}@{}'.format(
            user.username,
            hostname,
            )

    # FIXME Header and icon

    user.save()

    return user

on_actor = on_person
