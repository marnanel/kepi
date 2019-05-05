from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_kepi.validation import IncomingMessage
from django_kepi.find import find
from django_kepi.activity_model import Activity
from httpsig.verify import HeaderVerifier
import logging

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
