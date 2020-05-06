# delivery.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This module contains deliver(), which delivers objects
to their audiences.
"""

from celery import shared_task
import logging
import requests
import json
import httpsig
import random
from django.http.request import HttpRequest
from django.conf import settings
from kepi.bowler_pub.utils import configured_url, as_json, is_local

"""
from __future__ import absolute_import, unicode_literals
from kepi.bowler_pub.utils import is_local
import kepi.bowler_pub.models
from urllib.parse import urlparse
import django.urls
import django.utils.datastructures
import datetime
import pytz
from httpsig.verify import HeaderVerifier
from collections.abc import Iterable
""" # FIXME

logger = logging.getLogger(name='kepi')

def _rfc822_datetime(when=None):
    """
    Formats a datetime to the RFC822 standard.

    (The standard is silly, because GMT should be UTC,
    but we have to use it anyway.)
    """
    if when is None:
        when = datetime.datetime.utcnow()
    else:
        when.replace(tzinfo=pytz.UTC)

    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %T GMT")

def _find_local_actor(activity_form):
    """
    Given an activity, as a dict, return the local AcActor
    who apparently created it. If there is no such AcActor,
    or if the AcActor is remote, or if there's no Actor
    at all, return None.

    If the activity has no "actor" field, we use
    the "attributedTo" field.
    """

    from kepi.bowler_pub.models.acobject import AcObject

    parts = None
    for fieldname in ['actor', 'attributedTo']:
        if fieldname in activity_form:
            value = activity_form[fieldname]

            if isinstance(value, AcObject):
                return value
            else:
                parts = urlparse(activity_form[fieldname])
                break

    if parts is None:
        return None

    if parts.hostname not in settings.ALLOWED_HOSTS:
        return None

    return find_local(parts.path)

def _recipients_to_inboxes(recipients,
        local_actor=None):
    """
    Find inbox URLs for a set of recipients.

    "recipients" is an iterable of strings, each the ID of
    a recipient of a message. (These IDs will be URLs.)

    Returns a set of strings of URLs for their inboxes.
    Shared inboxes are preferred. This being a set,
    there will be no duplicates.
    """

    from kepi.bowler_pub import PUBLIC_IDS

    logger.info('Looking up inboxes for: %s',
            recipients)

    inboxes = set()

    recipients = sorted(list(recipients))

    original_recipients = recipients.copy()

    for recipient in recipients:

        if recipient in PUBLIC_IDS:
            if local_actor is not None:
                logger.debug('  -- treating public as %s\'s outbox',
                        local_actor)
                inboxes.add(local_actor['outbox'])
            else:
                logger.debug('  -- ignoring public')
            continue

        discovered = find(recipient)

        if discovered is None:
            logger.debug('  -- "%s" doesn\'t exist; dropping',
                    recipient)
            continue

        logger.debug('  -- "%s" found as %s',
                recipient, discovered)

        if is_local(recipient):

            if hasattr(discovered, 'first'):
                logger.debug('  -- %s is a local collection',
                        recipient)

                new_recipients = set([f.follower for f in discovered])

                new_recipients = new_recipients.difference(
                        original_recipients)

                logger.debug('  -- we add: %s',
                        new_recipients)

                recipients.extend(new_recipients)

            else:
                logger.debug('  -- %s is local; use directly',
                        recipient)
                inboxes.add(recipient)

            continue

        # so, it exists and it's remote

        if 'type' not in discovered:
            logger.debug('    -- has no type (weird)')

        elif discovered['type'] in ['Collection', 'OrderedCollection']:

            if recipient not in original_recipients:
                logger.debug('    -- is a collection, but we\'re too deep; ignoring')
                continue

            logger.debug('    -- is a collection')

            # XXX add checks to make sure we don't loop forever on duff data
            page_url = discovered.get('first', None)

            while page_url is not None:
                logger.debug('    -- loading page %s', page_url)
                page = find(page_url)
                page_url = None
                items = []

                if page is None:
                    logger.debug('      -- and that\'s missing')
                elif page.get('type', None) not in ['CollectionPage', 'OrderedCollectionPage']:
                    logger.debug('      -- which has a weird type; ignoring')
                elif page.get('partOf', None)!=recipient:
                    logger.debug('      -- which belongs to someone else; ignoring')
                elif 'orderedItems' in page:
                    items = page['orderedItems']
                elif 'items' in page:
                    items = page['items']

                if items:
                    logger.debug('      -- items are %s', items)
                    for item in items:
                        if item not in recipients:
                            logger.debug('        -- adding %s to recipients', item)
                            recipients.append(item)

                if page is not None:
                    page_url = page.get('next', None)

            logger.debug('    -- all loaded')

        elif discovered['type'] in ['Actor', 'Person']:

            if 'endpoints' in discovered and \
                    isinstance(discovered['endpoints'], Iterable) and \
                    'sharedInbox' in discovered['endpoints']:
                logger.debug('    -- has a shared inbox at %s',
                        discovered['endpoints']['sharedInbox'])
                inboxes.add(discovered['endpoints']['sharedInbox'])

            elif 'inbox' in discovered and discovered['inbox'] is not None:
                logger.debug('    -- has a sole inbox at %s',
                        discovered['inbox'])
                inboxes.add(discovered['inbox'])

            else:
                logger.debug('    -- has no obvious inbox; dropping')
        else:
            logger.warn('    -- remote object is an unexpected type')

    logger.info('Found inboxes: %s', inboxes)

    return inboxes

def _activity_form_to_outgoing_string(activity_form):
    """
    Formats an activity ready to be sent out as
    an HTTP response.
    """

    from kepi.bowler_pub import ATSIGN_CONTEXT
    from kepi.bowler_pub.utils import as_json

    format_for_delivery = activity_form.copy()
    for blind_field in ['bto', 'bcc']:
        if blind_field in format_for_delivery: 
            del format_for_delivery[blind_field]

    if '@context' not in format_for_delivery:
        format_for_delivery['@context'] = ATSIGN_CONTEXT

    message = as_json(
            format_for_delivery,
            )

    return message

def _signer_for_local_actor(local_actor):

    """
    Given an Actor object representing a local actor,
    return an httpsig.HeaderSigner object which can
    sign headers for them.
    """

    if local_actor is None:
        logger.info('not signing outgoing messages because we have no known actor')
        return None

    if local_actor.privateKey is None:
        logger.warn('not signing outgoing messages because local actor %s '+\
                'has no private key!', local_actor)
        return None

    try:
        return httpsig.HeaderSigner(
                key_id=local_actor.key_name,
                secret=local_actor.privateKey,
                algorithm='rsa-sha256',
                headers=['(request-target)', 'host', 'date', 'content-type'],
                sign_header='signature',
                )
    except httpsig.utils.HttpSigException as hse:
        logger.warn('Local private key was not honoured.')
        logger.warn('This should never happen!')
        logger.warn('Error was: %s', str(hse))
        logger.warn('Key was: %s', local_actor.privateKey)
        return None

class LocalDeliveryRequest(HttpRequest):

    """
    These are fake HttpRequests which we send to the views
    as an ACTIVITY_STORE method. For more information,
    see the docstring in views/.
    """

    def __init__(self, content, activity, path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.method = 'ACTIVITY_STORE'
        self.headers = {
            'Content-Type': 'application/activity+json',
            }
        self._content = bytes(content, encoding='UTF-8')
        self.activity = activity
        self.path = path

    @property
    def body(self):
        return self._content

def _deliver_local(
        activity,
        inbox,
        parsed_target_url,
        message,
        ):

    """
    Deliver an activity to a local actor.

    Keyword arguments:
    activity -- the activity we're delivering.
    inbox -- the URL of the inbox, only used in logging
    parsed_target_url -- the result of urlparse(url)
    message -- the activity as a formatted string
        (as it would appear if we were sending this out over HTTP)
    """

    logger.debug('%s: %s is local',
            activity, inbox)

    try:
        resolved = django.urls.resolve(parsed_target_url.path)
    except django.urls.Resolver404:
        logger.debug('%s: -- not found', parsed_target_url.path)
        return

    logger.debug('%s is handled by %s',
            parsed_target_url.path, resolved)

    request = LocalDeliveryRequest(
            content = message,
            activity = activity,
            path = parsed_target_url.path,
            )

    result = resolved.func(request,
            **resolved.kwargs,
            local = True,
            )

    if result:
        logger.debug('%s: resulting in %s %s', parsed_target_url.path,
                result.status_code, result.reason_phrase)
    else:
        logger.debug('%s: done', parsed_target_url.path)


def _deliver_remote(
        activity,
        inbox,
        parsed_target_url,
        message,
        signer,
        ):

    """
    Deliver an activity to a remote actor.

    Keyword arguments:
    activity -- the activity we're delivering.
    inbox -- the URL of the inbox
    parsed_target_url -- the result of urlparse(url)
    message -- the activity as a formatted string
        (as it would appear if we were sending this out over HTTP)
    signer -- an httpsig.HeaderSigner for the
        local actor who sent this activity, or None
        if there isn't one.
    """

    headers = {
            'Date': _rfc822_datetime(),
            'Host': parsed_target_url.netloc,
            # lowercase is deliberate, to work around
            # an infelicity of the signer library
            'content-type': "application/activity+json",
            }

    if signer is not None:
        headers = signer.sign(
                headers,
                method = 'POST',
                path = parsed_target_url.path,
                )

    logger.debug('%s: %s: headers are %s',
            activity, inbox, headers)

    response = requests.post(
            inbox,
            data=message,
            headers=headers,
            )

    logger.debug('%s: %s: posted. Server replied: %s %s',
            activity, inbox, response.status_code, response.reason)

    if response.status_code>=400 and response.status_code<=499 and \
            (response.status_code not in [404, 410]):

        # The server thinks we made an error. Log the request we made
        # so that we can debug it.

        logger.debug("  -- for debugging: our signer was %s",
                signer.__dict__)
        logger.debug("  -- and this is how the message ran:")
        logger.debug("%s\n%s", headers, message)

@shared_task()
def deliver(
        activity,
        ):

    """
    Deliver an activity to an actor.

    Keyword arguments:
        activity -- a dict representing an ActivityPub activity.

    This function is a shared task; it will be run by Celery behind
    the scenes.
    """

    import kepi.sombrero_sendpub.models as sombrero_models
    from kepi.bowler_pub import PUBLIC_IDS

    message = sombrero_models.OutgoingActivity(
            content=activity,
            )
    message.save()

    logger.info('activity %d: begin delivery: %s',
            message.pk, message.content)

    recipients = set()
    for field in ['to', 'bto', 'cc', 'bcc', 'audience']:
        if field in activity:
            for recipient in activity[field]:
                if not is_local(recipient):
                    recipients.update(activity[field])

    if not recipients:
        logger.debug('activity %d: there are no recipients; giving up',
                message.pk)
        return

    logger.debug('activity %d: recipients are %s',
            activity, recipients)

    # Dereference collections.

    inboxes = _recipients_to_inboxes(recipients,
            local_actor=activity['actor'])

    if not inboxes:
        logger.debug('activity %s: there are no inboxes to send to; giving up',
                message.pk)
        return

    logger.debug('%s: inboxes are %s',
            activity, inboxes)

    ############################
    raise ValueError("XXX TO HERE") # XXX TO HERE
    ############################

    message = _activity_form_to_outgoing_string(
            activity_form = activity_form,
            )

    signer = _signer_for_local_actor(
            local_actor = local_actor,
            )

    for inbox in inboxes:
        logger.debug('%s: %s: begin delivery',
                activity, inbox)

        if inbox is None:
            logger.warn('  -- attempt to deliver to None (but why?)')
            continue

        if inbox in PUBLIC_IDS:
            logger.debug("  -- mustn't deliver to Public")
            continue

        if is_local(inbox):
            _deliver_local(
                    activity,
                    inbox,
                    parsed_target_url,
                    message,
                    )
        else:

            if incoming:
                logger.debug('  -- target is remote; ignoring')
                continue

            _deliver_remote(
                    activity,
                    inbox,
                    parsed_target_url,
                    message,
                    signer,
                    )

    logger.debug('%s: message posted to all inboxes',
            activity)
