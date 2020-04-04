from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from kepi.bowler_pub.create import create
import kepi.bowler_pub.crypto as crypto
from kepi.bowler_pub.utils import uri_to_url
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import logging

logger = logging.Logger('kepi')

class Follow(models.Model):

    follower = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            related_name = 'following',
            )

    following = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            related_name = 'followers',
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
                    follower,
                    following,
                    )
        else:
            return '[%s follows %s]' % (
                    follower,
                    following,
                    )
