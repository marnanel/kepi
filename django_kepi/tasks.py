from __future__ import absolute_import, unicode_literals
from celery import shared_task
from django_kepi.validation import IncomingMessage
from django_kepi import find
import logging

logger = logging.getLogger(name='django_kepi')

@shared_task()
def validate(
        message_id,
        ):
    logger.info('%s: begin validation',
            message_id)

    message = IncomingMessage.objects.find(id=message_id)

    actor = message.actor
    key_id = message.key_id

    logger.debug('%s: message signature is: %s',
            message, message.signature)
    logger.debug('%s: message body is: %s',
            message, message.body)

    if _is_local_user(actor):
        logger.debug('%s: actor %s is local', message, actor)

        local_user = find(actor, 'Actor')

        if local_user is None:
            logger.info('%s: local actor %s does not exist; dropping message',
                message, actor)
            return

        key = local_user.key
        _do_validation(message, key)
        return

    if not _obviously_belongs_to(actor, key_id):
        logger.info('%s: key_id %s is not obviously owned by '+\
                'actor %s; dropping message',
                message, key_id, actor)
        return

    try:
        remote_key = CachedRemoteUser.objects.get(owner=actor)
    except CachedRemoteUser.DoesNotExist:
        remote_key = None

    if remote_key is not None:

        if remote_key.is_gone():
            # XXX This should probably trigger a clean-out of everything
            # we know about that user
            logger.info('%s: remote actor %s is gone; dropping message',
                    actor, message)
            return

        logger.debug('%s: we have the remote key', message)
        _do_validation(message, remote_key.key)
        return

    logger.debug('%s: we don\'t have the key', message)

    if second_pass:
        logger.warning('%s: we apparently both do and don\'t have the key',
                message)
        return

    message.waiting_for = actor
    message.save()

    if len(IncomingMessage.objects.filter(waiting_for=actor))==1:
        logger.debug('%s: starting background task', message)
        _kick_off_background_fetch(actor)
    else:
        logger.debug('%s: not starting background task', message)

