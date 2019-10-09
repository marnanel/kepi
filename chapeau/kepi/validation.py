# validation.py
#
# Part of chapeau, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This contains validate(), which checks whether an incoming
message is from who it claims to be from.
"""

from django.db import models
from celery import shared_task
import logging
import json
import uuid
import re
from django.conf import settings
from urllib.parse import urlparse
import django.core.exceptions
from httpsig.verify import HeaderVerifier

logger = logging.getLogger(name='chapeau')

class IncomingMessage(models.Model):

    """
    Incoming messages, while they're being validated.

    At present, we don't delete them afterwards. This is
    so we can use them for forensics when stuff goes wrong.
    But eventually we'll need kepi to clear up after itself.

    The primary key is a UUID because it helps with logging.
    You can't use any of the fields from the message to identify it,
    because we don't yet know whether it's telling the truth.
    """

    id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
            )

    received_date = models.DateTimeField(auto_now_add=True, blank=True)

    content_type = models.CharField(max_length=255, default='')
    date = models.CharField(max_length=255, default='')
    host = models.CharField(max_length=255, default='')
    path = models.CharField(max_length=255, default='')
    signature = models.CharField(max_length=255, default='')
    body = models.TextField(default='')
    key_id = models.CharField(max_length=255, default='')
    digest = models.CharField(max_length=255, default='')
    is_local_user = models.BooleanField(default=False)

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
        return '%s %s' % (self.id, self.received_date)

    @property
    def fields(self):
        try:
            return self._fields
        except AttributeError:
            self._fields = json.loads(self.body)
            logger.info('%s: fields are %s',
                    self, self._fields)
            return self._fields

    @property
    def activity_form(self):
        return self.fields

def validate(path, headers, body, is_local_user):

    """
    Validates a message.

    This function sets up the message for validation,
    kicks off the validation task, and returns immediately.
    The actual work is done by _run_validation(), below.

    path -- the URL path that the message was sent to
    headers -- the HTTP headers
    body -- the content of the message, as bytes or str
    is_local_user -- whether the source is local; this
        only exists so we can pass it to create() if
        the message is validated.
    """

    if isinstance(body, bytes):
        body = str(body, encoding='UTF-8')

    logger.info('Begin validation. Body is %s',
            body)
    logger.info('and headers are %s',
            headers)

    # make sure this is a real dict.
    # httpsig.utils.CaseInsensitiveDict doesn't
    # reimplement get(), which cases confusion.
    headers = dict([(f.lower(), v)
        for f,v in headers.items()])

    message = IncomingMessage(
            content_type = headers['content-type'],
            date = headers.get('date', ''),
            host = headers.get('host', ''),
            path = path,
            signature = headers.get('signature', ''),
            digest = headers.get('digest', ''),
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

    """
    Validates a message. Don't call this function directly;
    call validate(), above.

    If the message is successfully validated, we will
    pass it to create() to turn it into a Kepi object.
    If that's successful, we pass the new object to deliver().

    message_id -- the primary key of an IncomingMessage
        that was generated by validate().
    """

    from chapeau.kepi.delivery import deliver
    from chapeau.kepi.create import create
    from chapeau.kepi.find import find

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
        actor = find(message.actor)
    except json.decoder.JSONDecodeError as jde:
        logger.info('%s: invalid JSON; dropping: %s',
                message, jde)
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

    try:
        key = actor['publicKey']
        key = key['publicKeyPem']
    except TypeError as te:
        logger.info('%s: actor has an invalid public key (%s); dropping message',
                message, te,
                )
        return None

    logger.debug('Verifying; key=%s, path=%s, host=%s',
            key, message.path, message.host)

    logger.debug('All params: %s', {
            'headers': {
                'Content-Type': message.content_type,
                'Date': message.date,
                'Signature': message.signature,
                'Host': message.host,
                'Digest': message.digest,
                },
            'secret': key,
            'method': 'POST',
            'path': message.path,
            'host': message.host,
            'sign_header': 'Signature',
            })

    hv = HeaderVerifier(
            headers = {
                'Content-Type': message.content_type,
                'Date': message.date,
                'Signature': message.signature,
                'Host': message.host,
                'Digest': message.digest,
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

    result = create(
            sender=actor,
            is_local_user = message.is_local_user,
            **(message.activity_form),
            run_delivery = True,
            incoming = True,
            )

    if result is None:
        logger.info('%s: creation was refused; bailing', message)
        return

    logger.info('%s: produced new Thing %s', message, result)

    return result