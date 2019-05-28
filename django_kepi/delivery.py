from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_kepi.find import find, find_local
from django_kepi.models.thing import Thing
from httpsig.verify import HeaderVerifier
from urllib.parse import urlparse
from django.http.request import HttpRequest
from django.conf import settings
import logging
import requests
import json
import datetime
import pytz
import httpsig

logger = logging.getLogger(name='django_kepi')

def _rfc822_datetime(when=None):
    if when is None:
        when = datetime.datetime.utcnow()
    else:
        when.replace(tzinfo=pytz.UTC)

    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %T GMT")

def _find_local_actor(activity_form):
    path = urlparse(activity_form['actor']).path
    return find_local(path)

def _recipients_to_inboxes(recipients):

    inboxes = set()

    for recipient in recipients:

        # FIXME treat magic recipients specially

        actor = find(recipient)

        # FIXME this can also be a collection
        # FIXME this doesn't work when actor is local

        if actor is None:
            logger.debug('recipient "%s" doesn\'t exist; dropping',
                    recipient)
            continue

        if 'endpoints' in actor and 'sharedInbox' in actor['endpoints']:
            logger.debug('recipient "%s" has a shared inbox at %s',
                    recipient, actor['endpoints']['sharedInbox'])
            inboxes.add(actor['endpoints']['sharedInbox'])

        elif 'inbox' in actor:
            logger.debug('recipient "%s" has a sole inbox at %s',
                    recipient, actor['inbox'])
            inboxes.add(actor['endpoints']['sharedInbox'])

        else:
            logger.debug('recipient "%s" has no obvious inbox; dropping',
                    recipient)

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
            secret=local_actor.privateKey,
            algorithm='rsa-sha256',
            headers=['(request-target)', 'host', 'date', 'content-type'],
            )

@shared_task()
def deliver(
        activity_id,
        ):
    try:
        activity = Thing.objects.get(number=activity_id)
    except Thing.DoesNotExist:
        logger.warn("Can't deliver activity %s because it doesn't exist",
                activity_id)
        return None

    logger.info('%s: begin delivery',
            activity)

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
    if activity_form['actor'] in recipients:
        recipients.remove(activity_form['actor'])

    if not recipients:
        logger.debug('%s: there are no recipients; giving up',
                activity)
        return

    logger.debug('%s: recipients are %s',
            activity, recipients)

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

    # XXX this is getting complicated; refactor
    for inbox in inboxes:
        logger.debug('%s: %s: begin delivery',
                activity, inbox)

        parsed_target_url = urlparse(inbox,
                allow_fragments = False,
                )
        is_local = parsed_target_url.hostname in settings.ALLOWED_HOSTS

        if is_local:

            logger.debug('%s: %s is local',
                    activity, inbox)

            try:
                resolved = django.urls.resolve(parsed_target_url.path)
            except django.urls.Resolver404:
                logger.debug('%s: -- not found', path)
                continue
        
            request = LocalDeliveryRequest(
                    # ... XXX something goes here
                    )
            result = resolved.func(request,
                    **resolved.kwargs)
            logger.debug('%s: resulting in %s', path, result)
            continue
 
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

        logger.debug('%s: %s: posted. Server replied: %s',
                activity, inbox, response)

    logger.debug('%s: message posted to all inboxes',
            activity)