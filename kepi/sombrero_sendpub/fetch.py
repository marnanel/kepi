# fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

import requests
import django.db.utils
from django.http.request import HttpRequest
from django.conf import settings
from urllib.parse import urlparse
from kepi.trilby_api.models import *
from kepi.bowler_pub.utils import log_one_message
from kepi.bowler_pub.activityresponse import ActivityResponse
from kepi.sombrero_sendpub.webfinger import get_webfinger
import kepi.sombrero_sendpub.collections as sombrero_collections
from django.http import HttpResponse, JsonResponse, Http404

def fetch(address,
        expected_type,
        ):

    """
    Find remote or local objects.

    For remote objects, if we already know about them,
    return the existing object. If we don't, fetch it
    over the network and store it, then return the value.

    For local objects-- that is, ones where the hostname
    is listed in this project's ALLOWED_HOSTS setting--
    look it up locally and return it. If the address is
    a URL, this will pass through the dispatcher.

    "address" is the address of the thing we're looking for.
    It's usually a URL. For Persons it can also be atstyle
    ("username@hostname"), which will result in a webfinger
    lookup to find the actual URL. URLs should not contain
    an "@" sign.

    "expected_type" is the type we're looking for.

    "expected_type" should contain at least the fields
      - url (read/write)
      - status (write-only; for an HTTP status code)
      - local_form and remote_form, which may be identity functions

    Particular types of object may define handlers which
    can initialise other fields. The handler is looked up
    using the "type" field in the retrieved object,
    rather than the "expected_type" passed to this function.

    HTTP status codes are stored even for records that are
    rejected. (XXX This is an inconsistency: it means that
    the first time we look something rejected up, the record
    is stored but this function returns None; following times
    get the record returned, because it's cached. Fix and test.)
    Unreachable hosts and timeouts result in a status code of 0.

    This function returns the requested object if it can.
    If you didn't specify a type, raises ValueError.
    On all other errors, which are logged, returns None.
    """

    if address is None:
        return None

    wanted = _parse_address(address)

    wanted['type'] = expected_type

    if wanted['is_local']:
        handler = _fetch_local
    else:
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
        parsed = urlparse(address)
        result['hostname'] = parsed.netloc
        result['path'] = parsed.path

    result['is_local'] = result['hostname'] in settings.ALLOWED_HOSTS

    logger.debug("%s: wanted: %s", address, result)

    return result

def _fetch_local_by_atstyle(address, wanted):

    # atstyle only makes sense for Person
    if not issubclass(wanted['type'], Person):
        logger.warning("%s: atstyle request made for %s, not Person",
                address, wanted['type'])
        return None

    try:
        result = LocalPerson.objects.get(
                local_user__username = wanted['username'],
                )
        logger.info("%s: found local user: %s",
                address, result)
    except LocalPerson.DoesNotExist:
        logger.info("%s: no such user: %s",
                address, wanted['username'])
        result = None

    return result

def _fetch_local_by_url(address, wanted):
    from django.urls import resolve

    class ActivityRequest(HttpRequest):
        """
        These are fake HttpRequests which we send to the views
        as an ACTIVITY_GET method.
        """

        def __init__(self, path):
            super().__init__()

            self.path = path
            self.method = 'ACTIVITY_GET'

    try:
        resolved = resolve(wanted['path'])
    except django.urls.Resolver404:
        logger.info('%s: not found', address)
        return None

    logger.debug('%s: handled by %s, %s, %s',
            address,
            str(resolved.func),
            str(resolved.args),
            str(resolved.kwargs),
            )

    request = ActivityRequest(
            path=wanted['path'],
            )
    result = resolved.func(request,
            *resolved.args,
            **resolved.kwargs)

    logger.info("%s: result from handler was %s",
            address, result)

    if isinstance(result, ActivityResponse):
        result = result.activity_value

    if result is not None and not isinstance(result, wanted['type']):
        logger.info("%s: type mismatch (%s vs %s); discarding",
                address, type(result), wanted['type'],
                )
        return None

    return result

def _fetch_local(address, wanted):
    if wanted['is_atstyle']:
        return _fetch_local_by_atstyle(address, wanted)
    else:
        return _fetch_local_by_url(address, wanted)

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
        result = wanted['type'].remote_form().objects.get(
                **kwargs,
                )

        logger.debug("%s: already known: %s",
                address, result)

        return result

    except AttributeError:
        # Types don't have to support object lookup
        pass

    except wanted['type'].DoesNotExist:
        pass

    # No, so create them (but don't save yet).

    result = wanted['type'].remote_form()(
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
    except ValueError as ve:
        logger.info("%s: response was not JSON (%s); dropping",
                address, ve)

        if result is not None:
            result.status = 0
            result.save()

        return result

    log_one_message(
            direction = "retrieved",
            body = found,
            )

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
            ('following', 'following_url'),
            ('followers', 'followers_url'),
            ('inbox', 'inbox_url'),
            ('outbox', 'outbox_url'),
            ('featured', 'featured_url'),
            ('created_at', 'created_at'),
            ('bot', 'bot'),
            ('movedTo', 'moved_to'),
            ]:
        if foundname in found:
            setattr(user,
                    fieldname,
                    found[foundname])

    # A shared inbox takes priority over a personal inbox
    if 'endpoints' in found:
        if 'sharedInbox' in found['endpoints']:
            user.inbox_url = found['endpoints']['sharedInbox']

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

def on_collection(found, obj):
    obj.update(found)
    return obj

on_collection_page = on_collection
on_orderedcollection = on_collection
on_orderedcollectionpage = on_collection
