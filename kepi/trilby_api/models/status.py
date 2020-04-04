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

class Status(models.Model):

    # TODO: The original design has the serial number
    # monotonically but unpredictably increasing.

    remote_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            unique = True,
            )

    account = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            )

    in_reply_to_id = models.ForeignKey(
            'self',
            on_delete = models.DO_NOTHING,
            null = True,
            blank = True,
            )
    
    content = models.TextField(
        )

    created_at = models.DateTimeField(
            default = now,
            )

   # TODO Media

    sensitive = models.BooleanField(
            default = False,
            )

    spoiler_text = models.CharField(
            max_length = 255,
            null = True,
            blank = True,
            default = '',
            )

    visibility = models.CharField(
            max_length = 255,
            default = 'public',
            )

    language = models.CharField(
            max_length = 255,
            null = True,
            default = settings.KEPI['LANGUAGES'][0],
            )

    idempotency_key = models.CharField(
            max_length = 255,
            null = True,
            default = None,
            )

    @property
    def emojis(self):
        return [] # TODO

    @property
    def reblogs_count(self):
        return 0 # FIXME

    @property
    def favourites_count(self):
        return 0 # FIXME

    @property
    def reblogged(self):
        return False # FIXME

    @property
    def favourited(self):
        return False # FIXME

    @property
    def muted(self):
        return False # FIXME

    @property
    def pinned(self):
        return False # FIXME

    @property
    def media_attachments(self):
        return [] # FIXME

    @property
    def mentions(self):
        return [] # FIXME

    @property
    def tags(self):
        return [] # FIXME

    @property
    def card(self):
        return None # FIXME

    @property
    def poll(self):
        return None # FIXME

    @property
    def application(self):
        return None # FIXME

    @property
    def in_reply_to_account_id(self):
        return None # FIXME

    @property
    def uri(self):
        return 'FIXME' # FIXME

    @property
    def url(self):
        return 'FIXME' # FIXME

    @property
    def ancestors(self):
        return [] # FIXME

    @property
    def descendants(self):
        return [] # FIXME
