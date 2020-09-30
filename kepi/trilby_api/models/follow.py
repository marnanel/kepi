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

    """
    A record that someone follows someone else.
    """

    follower = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            related_name = 'rel_following',
            help_text = "The person who's following.",
            )

    following = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            related_name = 'rel_followers',
            help_text = "The person who's being followed.",
            )

    offer = models.URLField(
            max_length = 255,
            default = None,
            null = True,
            blank = True,
            help_text = "If this is an offer, the ID of the offer. "+\
                    "If this isn't an offer, None.",
            )

    show_reblogs = models.BooleanField(
            default=True,
            help_text = "True if the following person wants to see "+\
                    "reblogs from the follower. False if they only "+\
                    "want to see the follower's original posts.",
            )

    class Meta:
        constraints = [
                UniqueConstraint(
                    fields = ['follower', 'following'],
                    name = 'follow_only_once',
                    ),
                ]

    def __str__(self):
        if self.offer is not None:
            return '[%s requests to follow %s]' % (
                    self.follower,
                    self.following,
                    )
        else:
            return '[%s follows %s]' % (
                    self.follower,
                    self.following,
                    )
