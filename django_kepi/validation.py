from django.db import models
import logging
import json
import uuid
from django.conf import settings
from urllib.parse import urlparse
from django_kepi import find
from httpsig.verify import HeaderVerifier

logger = logging.getLogger(name='django_kepi')

# When we receive a message, M, in an inbox, we call validate(M).
#
# MESSAGE RECEIVED:
# Cases:
#   1) The claimed sender is a local user (i.e. their host is in ALLOWED_HOSTS).
#   2) The claimed sender is remote, and we have their key cached.
#   3) The claimed sender is remote, and we know that their account was closed.
#          (We know this because requesting their details has resulted in
#           a 410 error in the past.)
#   4) The claimed sender is remote, we have no information stored about
#           their key, and the claimed key obviously belongs to
#           the user. (This means, at present, that the key is in the
#           same remote document as the user's profile.)
#   5) The claimed sender is remote, we have no information stored about
#           their key, and the claimed key doesn't obviously belong to
#           the user.
#
# Behaviour:
#   1) Request the local user's key from the class which is handling Person.
#       Then go to VALIDATION below.
#   2) Go to VALIDATION below.
#   3) Drop the message.
#   4) Set our "waiting_for" record to the URL we need.
#       Save our IncomingMessage object.
#      If there is no existing request for that URL, create a background task
#           to retrieve its contents. Then go to BACKGROUND TASK FINISHED
#           below.
#   5) Report an error and drop the message.
#
# VALIDATION:
# Cases:
#   1) The message passes validation.
#   2) The message doesn't pass validation.
# Behaviour:
#   1) Call handle(M).
#   2) Drop the message.
#
# BACKGROUND TASK FINISHED:
# Cases:
#   1) We now have a remote user's key.
#       Cache the key;
#       For all IncomingMessages which are waiting on that key:
#           Pass it through to VALIDATION above.
#           Delete the IncomingMessage.
#   2) The remote user doesn't exist (410 Gone, or the host doesn't exist)
#       Store a blank in the key cache;
#       Drop the message.
#   3) Network issues.
#       If there's been fewer than "n" tries, recreate the background task.
#       Otherwise, report the error and drop the message.

class CachedPublicKey(models.Model):

    owner = models.URLField(
            )

    key = models.TextField(
            default = None,
            null = True,
            )

    # XXX We should probably also have a cache timeout

    def is_gone(self):
        return self.key is None

    def __str__(self):
        if self.key is None:
            return '(%s: public key)' % (self.owner)
        else:
            return '(%s is GONE)' % (self.owner)

class IncomingMessage(models.Model):

    id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
            )

    received_date = models.DateTimeField(auto_now_add=True, blank=True)

    content_type = models.CharField(max_length=255, default='')
    date = models.CharField(max_length=255, default='')
    digest = models.CharField(max_length=255, default='')
    host = models.CharField(max_length=255, default='')
    path = models.CharField(max_length=255, default='')
    signature = models.CharField(max_length=255, default='')
    body = models.TextField(default='')
    actor = models.CharField(max_length=255, default='')
    key_id = models.CharField(max_length=255, default='')

    waiting_for = models.URLField(default=None)

    def __str__(self):
        return str(self.id)

    @property
    def fields(self):
        return json.loads(self.body)

def is_local_user(url):
    return urlparse(url).hostname in settings.ALLOWED_HOSTS

def _obviously_belongs_to(actor, key_id):
    return key_id.startswith(actor+'#')

def _kick_off_background_fetch(url):
    # XXX actually do it
    pass

def _do_validation(message, key):
    logger.debug('%s: running actual validation', message)
    fields = message.fields
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
        return

    logger.info('%s: validation passed...', message)
    # XXX okay, go on, do something with it

def validate(message,
        second_pass=False):

    actor = message.actor
    key_id = message.key_id

    logger.debug('%s: begin validation; key_id is %s',
            message, key_id)
    logger.debug('%s: message signature is: %s',
            message, message.signature)
    logger.debug('%s: message body is: %s',
            message, message.body)

    if is_local_user(actor):
        logger.debug('%s: actor is local', message)

        local_user = find(actor, 'Actor')

        if local_user is None:
            logger.info('%s: local actor %s does not exist; dropping message',
                message, actor)
            return

        key = local_user.key
        _do_validation(message, key)
        return

    try:
        remote_key = CachedPublicKey.objects.get(owner=actor)
    except CachedPublicKey.DoesNotExist:
        remote_key = None

    if remote_key is not None:

        if remote_key.is_gone():
            # XXX This should probably trigger a clean-out of everything
            # we know about that user
            logger.info('%s: remote actor %s is gone; dropping message',
                    actor, message)
            return

        logger.debug('%s: we have the remote key', message)
        _do_validation(message, remote_key)
        return

    if not _obviously_belongs_to(actor, key_id):
        logger.info('%s: key_id %s is not obviously owned by '+\
                'actor %s; dropping message',
                message, key_id, actor)
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

