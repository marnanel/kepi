# validation.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This contains validate(), which checks whether an incoming
message is from who it claims to be from.
"""

import logging
logger = logging.getLogger(name="kepi")

from django.db import models
from celery import shared_task
import json
import re
from django.conf import settings
from urllib.parse import urlparse
import django.core.exceptions
import uuid
from httpsig.verify import HeaderVerifier
from kepi.sombrero_sendpub.fetch import fetch
from kepi.bowler_pub.create import create

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

def validate(path, headers, body):

    """
    Validates a message.

    This function sets up the message for validation,
    kicks off the validation task, and returns immediately.
    The actual work is done by _run_validation(), below.

    path -- the URL path that the message was sent to
    headers -- the HTTP headers
    body -- the content of the message, as bytes or str
    """

    import kepi.trilby_api.models as trilby_models

    logger.info('Begin validation. Body is %s',
            body)
    logger.info('and headers are %s',
            headers)

    if isinstance(body, bytes):
        try:
            # XXX It might not be UTF-8; we have to check the headers
            body = str(body, encoding='UTF-8')
        except UnicodeDecodeError as ude:
            logger.info("  -- failed validation: invalid encoding: %s",
                    ude)
            return

    # make sure this is a real dict.
    # httpsig.utils.CaseInsensitiveDict doesn't
    # reimplement get(), which cases confusion.
    headers = dict([(f.lower(), v)
        for f,v in headers.items()])

    message = IncomingMessage(
            content_type = headers.get('content-type',
                'application/activity+json'),
            date = headers.get('date', ''),
            host = headers.get('host', ''),
            path = path,
            signature = headers.get('signature', ''),
            digest = headers.get('digest', ''),
            body = body,
            )
    message.save()

    logger.debug('%s: invoking the validation task',
            message.id)
    _run_validation(message.id)

@shared_task()
def _run_validation(
        message_id,
        ):

    try:
        message = IncomingMessage.objects.get(id=message_id)
    except django.core.exceptions.ValidationError:
        # This is because celery tasks are loosely coupled to
        # the rest of the application, so we pass in only
        # primitive types.
        raise ValueError("_run_validation()'s message_id parameter takes a UUID string")

    valid = _run_validation_inner(message)

    if valid:
        result = create(message)
        return result

    return None

def _run_validation_inner(
        message,
        ):

    """
    Validates a message. Don't call this function directly;
    call validate(), above.

    Returns True iff the message is valid.

    message_id -- the primary key of an IncomingMessage
        that was generated by validate().
    """

    logger.info('%s: begin validation',
            message)

    try:
        key_id = message.key_id
    except ValueError:
        logger.warning('%s: message is unsigned; dropping',
                message)
        return False

    try:
        from kepi.trilby_api.models import Person
        actor = fetch(message.actor,
                Person)
    except json.decoder.JSONDecodeError as jde:
        logger.info('%s: invalid JSON; dropping: %s',
                message, jde)
        return False
    except UnicodeDecodeError:
        logger.info('%s: invalid UTF-8; dropping', message)
        return False

    if actor is None or actor.status==404:
        logger.info('%s: remote actor does not exist; dropping message',
            message)
        return False
    elif actor.status==410:
        logger.info('%s: remote actor has Gone',
            message)
        # FIXME: If this message is an instruction to delete a remote user,
        # it's valid if the remote user is Gone.
        return False
    elif actor.status!=200:
        logger.info('%s: remote actor could not be fetched (status %d)',
            message, actor.status)
        return False

    logger.debug('%s: message signature is: %s',
            message, message.signature)
    logger.debug('%s: message body is: %s',
            message, message.body)

    logger.debug('%s: actor details are: %s',
            message, actor)

    # XXX key used to sign must "_obviously_belong_to" the actor

    try:
        key = actor.publicKey
    except TypeError as te:
        logger.info('%s: actor has an invalid public key (%s); dropping message',
                message, te,
                )
        return False

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
        return False

    logger.debug('%s: validation passed!', message)

    return True
