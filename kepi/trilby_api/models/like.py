# follow.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import kepi.bowler_pub.crypto as crypto
import kepi.trilby_api.signals as trilby_signals
from kepi.bowler_pub.utils import uri_to_url
from django.utils.timezone import now
from django.core.exceptions import ValidationError

class Like(models.Model):

    liker = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            )

    liked = models.ForeignKey(
            'Status',
            on_delete = models.DO_NOTHING,
            )

    class Meta:
        constraints = [
                UniqueConstraint(
                    fields = ['liker', 'liked'],
                    name = 'i_cant_like_this_enough',
                    ),
                ]

    def __str__(self):
        return '[%s likes %s]' % (liker, liked)

    def save(self,
            send_signal = False,
            *args, **kwargs):

        newly_made = self.pk is None

        super().save(*args, **kwargs)

        if send_signal and newly_made:
            logger.debug("%s: sending 'liked'", self)
            trilby_signals.liked.send(sender=self)

    def delete(self,
            send_signal = False,
            *args, **kwargs):

        if send_signal:
            logger.info("%s: sending 'unliked'", self)
            trilby_signals.unliked.send(sender=self)

        super().delete(*args, **kwargs)
