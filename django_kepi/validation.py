from django.db import models
from celery import shared_task
import logging
import json
import uuid
import re
from django.conf import settings
from urllib.parse import urlparse
import django_kepi.find
import django_kepi.create
import django.core.exceptions
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
    is_local_user = models.BooleanField(default=False)

    waiting_for = models.URLField(default=None, null=True)

    @property
    def actor(self):
        if 'actor' in self.fields:
            return self.fields['actor']
        else:
            return self.fields.get('attributedTo', '')

    @property
    def key_id(self):
        if not self.signature:
            logger.debug("%s:   -- message has no signature", self)
            raise ValueError("Can't get the key ID because this message isn't signed")

        try:
            return re.findall(r'keyId="([^"]*)"', self.signature)[0]
        except IndexError:
            logger.debug("%s:   -- message's signature has no keyID", self)
            raise ValueError("Key ID not found in %s" % (self.signature,))

    def __str__(self):
        return str(self.id)

    @property
    def fields(self):
        try:
            return self._fields
        except AttributeError:
            self._fields = json.loads(self.body)
            return self._fields

    @property
    def activity_form(self):
        return self.fields

def validate(path, headers, body, is_local_user):

    if isinstance(body, bytes):
        body = str(body, encoding='UTF-8')

    message = IncomingMessage(
            content_type = headers['content-type'],
            date = headers.get('date', ''),
            digest = '', # FIXME ???
            host = headers.get('host', ''),
            path = path,
            signature = headers.get('Signature', ''),
            body = body,
            is_local_user = is_local_user,
            )
    message.save()

    logger.debug('%s: invoking the validation task',
            message.id)
    _run_validation(message.id)
    logger.debug('%s: finished invoking the validation task',
            message.id)

@shared_task()
def _run_validation(
        message_id,
        ):

    from django_kepi.delivery import deliver

    logger.info('%s: begin validation',
            message_id)

    try:
        message = IncomingMessage.objects.get(id=message_id)
    except django.core.exceptions.ValidationError:
        # This is because celery tasks are loosely coupled to
        # the rest of the application, so we pass in only
        # primitive types.
        raise ValueError("_run_validation()'s message_id parameter takes a UUID string")

    try:
        key_id = message.key_id
    except ValueError:
        logger.warn('%s: message is unsigned; dropping',
                message)
        return None

    try:
        actor = django_kepi.find.find(message.actor)
    except json.decoder.JSONDecodeError:
        logger.info('%s: invalid JSON; dropping', message)
        return None
    except UnicodeDecodeError:
        logger.info('%s: invalid UTF-8; dropping', message)
        return None

    if actor is None:
        logger.info('%s: actor does not exist; dropping message',
            message)
        return None

    logger.debug('%s: message signature is: %s',
            message, message.signature)
    logger.debug('%s: message body is: %s',
            message, message.body)

    logger.debug('%s: actor details are: %s',
            message, actor)

    # XXX key used to sign must "_obviously_belong_to" the actor

    key = actor['publicKey']
    key = key['publicKeyPem']
    logger.debug('Verifying; key=%s, path=%s, host=%s',
            key, message.path, message.host)

    hv = HeaderVerifier(
            headers = {
                'Content-Type': message.content_type,
                'Date': message.date,
                'Signature': message.signature,
                'Host': message.host,
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

    result = django_kepi.create.create(
            sender=actor,
            is_local_user = message.is_local_user,
            **(message.activity_form),
            )

    if result is None:
        logger.info('%s: creation was refused; bailing', message)
        return

    logger.info('%s: produced new Thing %s', message, result)

    deliver(result.number,
            incoming = True)

    return result
