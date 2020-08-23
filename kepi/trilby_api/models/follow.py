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
from kepi.bowler_pub.utils import uri_to_url
from django.utils.timezone import now
from django.core.exceptions import ValidationError

class Follow(models.Model):

    follower = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            related_name = 'rel_following',
            )

    following = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            related_name = 'rel_followers',
            )

    requested = models.BooleanField(
            default=True,
            )

    show_reblogs = models.BooleanField(
            default=True,
            )

    class Meta:
        constraints = [
                UniqueConstraint(
                    fields = ['follower', 'following'],
                    name = 'follow_only_once',
                    ),
                ]

    def __str__(self):
        if self.requested:
            return '[%s requests to follow %s]' % (
                    self.follower,
                    self.following,
                    )
        else:
            return '[%s follows %s]' % (
                    self.follower,
                    self.following,
                    )
