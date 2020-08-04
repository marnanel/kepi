# fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

import requests
import django.db.utils
from urllib.parse import urlparse
from kepi.trilby_api.models import RemotePerson
from kepi.sombrero_sendpub.webfinger import get_webfinger

def fetch(address,
        expected_type = None):

    # TODO What if the URL is local?

    if expected_type is None:
        result = None
    else:

        # Do they already exist?

        if '@' in address:
            kwargs = {"acct": address}
        else:
            kwargs = {"url": address}

        try:
            result = expected_type.objects.get(
                    **kwargs,
                    )
            # Yes.
            return result
        except expected_type.DoesNotExist:
            pass

        # No, so create them (but don't save yet).

        result = expected_type(
                **kwargs,
                )

    if '@' in address:

        fields = address.split('@')

        webfinger = get_webfinger(
                username=fields[-2],
                hostname=fields[-1],
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
        details = response.json()
    except ValueError:
        logger.info("%s: response was not JSON",
                address)

        if result is not None:
            result.status = 0
            result.save()

        return result

    if 'type' not in details:
        logger.info("%s: retrieved JSON did not include a type",
                address)

        if result is not None:
            result.status = 0
            result.save()

        return result

    if 'id' in details:
        if details['id'] != address:
            logger.info(
                    "%s: user's id was not the source url: got %s",
                    address, details['id'],
                    )
            result.status = 0
            result.save()

            return result

    # Do we have a handler to finish up with?

    handler_name = 'on_%s' % (
            details['type'].lower(),
            )

    if handler_name in globals():

        try:
            result = globals()[handler_name](details, result)
            logger.info("%s: result was %s",
                    address, result)
        except ValueError as ve:
            logger.info("%s: %s from handler; returning None",
                    address, ve)
            return None

        if expected_type is not None and \
                not isinstance(result, expected_type):

                    logger.info("%s:    -- which wasn't %s; returning None",
                            address, expected_type)

                    return None

        return result

    else:

        # no handler

        if result is None:
            logger.info("%s: no %s; returning %s",
                    address, handler_name, result)
            return result
        else:
            logger.info("%s: no %s; returning dict",
                    address, handler_name)
            return details

def on_person(details, user):

    for detailsname, fieldname in [
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
        if detailsname in details:
            setattr(user,
                    fieldname,
                    details[detailsname])

    # A shared inbox takes priority over a personal inbox
    if 'endpoints' in details:
        if 'sharedInbox' in details['endpoints']:
            user.inbox = details['endpoints']['sharedInbox']

    if 'publicKey' in details:
        key = details['publicKey']

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
