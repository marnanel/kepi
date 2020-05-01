from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import kepi.bowler_pub.crypto as crypto
from kepi.bowler_pub.utils import uri_to_url
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import logging

logger = logging.Logger('kepi')

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
