from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_kepi.validation import IncomingMessage
from django_kepi.find import find
from django_kepi.activity_model import Activity
from httpsig.verify import HeaderVerifier
import logging
import requests
import json

logger = logging.getLogger(name='django_kepi')

@shared_task()
def validate(
        message_id,
        ):
    logger.info('%s: begin validation',
            message_id)

    message = IncomingMessage.objects.get(id=message_id)

    logger.debug('%s: received %s',
            message_id, str(message))

    actor = message.actor
    key_id = message.key_id

    logger.debug('%s: message signature is: %s',
            message, message.signature)
    logger.debug('%s: message body is: %s',
            message, message.body)

    actor_details = find(actor)

    logger.debug('%s: actor details are: %s',
            message, actor_details)

    if actor_details is None:
        logger.info('%s: actor %s does not exist; dropping message',
            message, actor)
        return None

    # XXX key used to sign must "_obviously_belong_to" the actor

    key = actor_details.public_key

    logger.debug('%s: public key is: %s',
            message, key)

    hv = HeaderVerifier(
            headers = {
                'Content-Type': message.content_type,
                'Date': message.date,
                'Signature': message.signature,
                },
            secret = key,
            method = 'POST',
            path = message.path,
            host = message.host,
            sign_header = 'Signature',
        )

    if not hv.verify():
        logger.info('%s: spoofing attempt; message dropped',
                message)
        return None

    logger.debug('%s: validation passed!', message)

    result = Activity.create(
            value=message.activity_form,
            sender=actor,
            )
    logger.debug('%s: produced new Activity %s', message, result )
    return result

@shared_task()
def deliver(
        activity_id,
        ):
    try:
        activity = Activity.objects.get(uuid=activity_id)
    except Activity.DoesNotExist:
        logger.warn("Can't deliver activity %s because it doesn't exist",
                activity_id)
        return None

    logger.info('%s: begin delivery',
            activity)

    activity_form = activity.activity_form
    logger.debug('%s: full form is %s',
            activity, activity_form)

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

    inboxes = set()

    for recipient in recipients:
        actor_details = find(recipient)

        if actor_details is None:
            logger.debug('%s: recipient "%s" doesn\'t exist; dropping',
                    activity, recipient)
            continue

        if 'endpoints' in actor_details and 'sharedInbox' in actor_details['endpoints']:
            logger.debug('%s: recipient "%s" has a shared inbox at %s',
                    activity, recipient, actor_details['endpoints']['sharedInbox'])
            inboxes.add(actor_details['endpoints']['sharedInbox'])

        elif 'inbox' in actor_details:
            logger.debug('%s: recipient "%s" has a sole inbox at %s',
                    activity, recipient, actor_details['inbox'])
            inboxes.add(actor_details['endpoints']['sharedInbox'])

        else:
            logger.debug('%s: recipient "%s" has no obvious inbox; dropping',
                    activity, recipient)

    if not inboxes:
        logger.debug('%s: there are no inboxes to send to; giving up',
                activity)
        return

    logger.debug('%s: inboxes are %s',
            activity, inboxes)

    format_for_delivery = activity_form.copy()
    for blind_field in ['bto', 'bcc']:
        if blind_field in format_for_delivery: 
            del format_for_delivery[blind_field]

    # FIXME
    # FIXME This is where we sign the message!
    # FIXME

    message = json.dumps(
            format_for_delivery,
            sort_keys = True,
            indent = 2,
            )

    for inbox in inboxes:
        logger.debug('%s: %s: begin delivery',
                activity, inbox)
        requests.post(
                inbox,
                data=message,
                headers={
                    'Content-Type': 'application/activity+json',
                    },
                )
        logger.debug('%s: %s: posted',
                activity, inbox)

    logger.debug('%s: message posted to all inboxes',
            activity)
