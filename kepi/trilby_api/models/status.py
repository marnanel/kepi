from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import kepi.bowler_pub.crypto as crypto
from kepi.bowler_pub.utils import uri_to_url
import kepi.trilby_api.utils as trilby_utils
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import logging

logger = logging.Logger('kepi')

class Status(models.Model):

    class Meta:
        verbose_name_plural = 'Statuses'

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
            related_name = 'poster',
            on_delete = models.DO_NOTHING,
            )

    in_reply_to = models.ForeignKey(
            'self',
            related_name = 'replies',
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
            max_length = 1,
            default = trilby_utils.VISIBILITY_PUBLIC,
            choices = trilby_utils.VISIBILITY_CHOICES,
            help_text = """Visiblity of this status.

            Public (A): visible to anyone.
            Unlisted (U): visible to anyone, but
                doesn't appear in timelines.
            Private (X): only visible to followers.
            Direct (D): visible to nobody except tagged people.

            Additionally, a person tagged in a status can
            always view that status.""",
            )

    language = models.CharField(
            max_length = 255,
            null = True,
            default = settings.KEPI['LANGUAGES'][0],
            )

    reblog_of = models.ForeignKey(
        'self',
        related_name = 'reblogs',
        on_delete = models.CASCADE,
        null = True,
        blank = True,
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
        # I know this property is called "uri", but
        # this matches the behaviour of Mastodon
        return self.url

    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return uri_to_url(settings.KEPI['STATUS_LINK'] % {
                'username': self.account.username,
                'id': self.id,
                })

    @property
    def ancestors(self):

        result = []
        parent = self.in_reply_to

        while parent is not None:
            result.insert(0, parent)
            parent = parent.in_reply_to

        return result

    @property
    def descendants(self):

        result = []
        current = self

        while True:
            try:
                child = Status.objects.get(
                        in_reply_to = current,
                        )
            except Status.DoesNotExist:
                break

            result.append(child)
            current = child

        return result

    def save(self, *args, **kwargs):

        if self.reblog_of == self:
            raise ValueError("Status can't be a reblog of itself")

        if self.in_reply_to == self:
            raise ValueError("Status can't be a reply to itself")

        super().save(*args, **kwargs)
