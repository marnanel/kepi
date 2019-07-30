from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_kepi.find import find, find_local
import django_kepi.models
from httpsig.verify import HeaderVerifier
from urllib.parse import urlparse
from django.http.request import HttpRequest
from django.conf import settings
import django.urls
import django.utils.datastructures
import logging
import requests
import json
import datetime
import pytz
import httpsig

logger = logging.getLogger(name='django_kepi.delivery')

# Magic IDs for public messages.
PUBLIC_ID_LIST = [
        'https://www.w3.org/ns/activitystreams#Public',
        'as:Public',
        'Public',
        ]

def _rfc822_datetime(when=None):
    if when is None:
        when = datetime.datetime.utcnow()
    else:
        when.replace(tzinfo=pytz.UTC)

    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %T GMT")

def _find_local_actor(activity_form):

    parts = None
    for fieldname in ['actor', 'attributedTo']:
        if fieldname in activity_form:
            parts = urlparse(activity_form[fieldname])
            break

    if parts is None:
        return None

    if parts.hostname not in settings.ALLOWED_HOSTS:
        return None

    return find_local(parts.path)

def _recipients_to_inboxes(recipients):
    """
    Find inbox URLs for a set of recipients.

    "recipients" is an iterable of strings, each the ID of
    a recipient of a message. (These IDs will be URLs.)

    Returns a set of strings of URLs for their inboxes.
    Shared inboxes are preferred. This being a set,
    there will be no duplicates.
    """

    logger.info('Looking up inboxes for: %s',
            recipients)

    inboxes = set()

    recipients = sorted(list(recipients))

    original_recipients = recipients.copy()

    for recipient in recipients:

        if recipient in PUBLIC_ID_LIST:
            logger.debug('  -- ignoring public')
            continue

        discovered = find(recipient)

        if discovered is None:
            logger.debug('  -- "%s" doesn\'t exist; dropping',
                    recipient)
            continue

        logger.debug('  -- "%s" found as %s',
                recipient, discovered)

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

            if 'endpoints' in discovered and 'sharedInbox' in discovered['endpoints']:
                logger.debug('    -- has a shared inbox at %s',
                        discovered['endpoints']['sharedInbox'])
                inboxes.add(discovered['endpoints']['sharedInbox'])

            elif 'inbox' in discovered:
                logger.debug('    -- has a sole inbox at %s',
                        discovered['inbox'])
                inboxes.add(discovered['inbox'])

            else:
                logger.debug('    -- has no obvious inbox; dropping')
        else:
            logger.warn('    -- remote object is an unexpected type')

    logger.info('Found inboxes: %s', inboxes)

    return inboxes

def _activity_form_to_outgoing_string(activity_form,
        local_actor = None):

    format_for_delivery = activity_form.copy()
    for blind_field in ['bto', 'bcc']:
        if blind_field in format_for_delivery: 
            del format_for_delivery[blind_field]

    message = json.dumps(
            format_for_delivery,
            sort_keys = True,
            indent = 2,
            )

    return message

def _signer_for_local_actor(local_actor):
    if local_actor is None:
        logger.info('not signing outgoing messages because we have no known actor')
        return None

    return httpsig.HeaderSigner(
            key_id=local_actor.key_name,
            secret=local_actor.f_privateKey,
            algorithm='rsa-sha256',
            headers=['(request-target)', 'host', 'date', 'content-type'],
            )

class LocalDeliveryRequest(HttpRequest):

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
    logger.debug('%s: %s is local',
            activity, inbox)

    try:
        resolved = django.urls.resolve(parsed_target_url.path)
    except django.urls.Resolver404:
        logger.debug('%s: -- not found', parsed_target_url.path)
        return

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

@shared_task()
def deliver(
        activity_id,
        incoming = False,
        ):
    try:
        activity = django_kepi.models.Thing.objects.get(number=activity_id)
    except django_kepi.models.Thing.DoesNotExist:
        logger.warn("Can't deliver activity %s because it doesn't exist",
                activity_id)
        return None

    logger.info('%s: begin delivery; incoming==%s',
            activity, incoming)

    activity_form = activity.activity_form
    logger.debug('%s: full form is %s',
            activity, activity_form)

    local_actor = _find_local_actor(activity_form)
    logger.debug('%s: local actor is %s',
            activity, local_actor)

    recipients = set()
    for field in ['to', 'bto', 'cc', 'bcc', 'audience']:
        if field in activity_form:
            recipients.update(activity_form[field])

    # Actors don't get told about their own activities
    if not incoming:
        if activity_form['actor'] in recipients:
            recipients.remove(activity_form['actor'])

    if not recipients:
        logger.debug('%s: there are no recipients; giving up',
                activity)
        return

    logger.debug('%s: recipients are %s',
            activity, recipients)

    if incoming:

        inboxes = recipients
        message = ''
        signer = None

    else:

        # Dereference collections.

        inboxes = _recipients_to_inboxes(recipients)

        if not inboxes:
            logger.debug('%s: there are no inboxes to send to; giving up',
                    activity)
            return

        logger.debug('%s: inboxes are %s',
                activity, inboxes)

        message = _activity_form_to_outgoing_string(
                activity_form = activity_form,
                local_actor = local_actor,
                )

        signer = _signer_for_local_actor(
                local_actor = local_actor,
                )

    for inbox in inboxes:
        logger.debug('%s: %s: begin delivery',
                activity, inbox)

        parsed_target_url = urlparse(inbox,
                allow_fragments = False,
                )
        is_local = parsed_target_url.hostname in settings.ALLOWED_HOSTS

        if is_local:
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
