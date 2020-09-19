# incoming.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

from django.db import models
import uuid
import json

class Incoming(models.Model):
    """
    Incoming messages, while they're being validated.

    At present, we don't delete them afterwards. This is
    so we can use them for forensics when stuff goes wrong.
    But eventually we'll need bowler_pub to clear up after itself.

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
