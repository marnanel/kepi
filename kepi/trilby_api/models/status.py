# status.py
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
from kepi.bowler_pub.utils import uri_to_url, is_local
import kepi.trilby_api.utils as trilby_utils
import kepi.trilby_api.signals as trilby_signals
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from polymorphic.models import PolymorphicModel

class Status(PolymorphicModel):

    class Meta:
        verbose_name_plural = 'Statuses'

    @classmethod
    def local_form(cls):
        return Status

    @classmethod
    def remote_form(cls):
        return Status

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
            help_text = "Visiblity of this status.\n\n"+\
                    trilby_utils.VISIBILITY_HELP_TEXT,
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
        return self.reblogs.count()

    @property
    def favourites_count(self):
        return 0 # FIXME

    @property
    def original(self):
        result = self.reblog_of

        if result is None:
            return self

        if result.reblog_of is not None:
            # Reblog of reblog, which is invalid
            return self

        return result

    @property
    def reblogged(self):
        return self.reblogs.exists()

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
    def conversation(self):
        return 'conversation' # FIXME

    @property
    def in_reply_to_account_id(self):
        return self.in_reply_to.account.id

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

    @property
    def thread(self):

        result = self.ancestors
        result.append(self)
        result.extend(self.descendants)

        return result

    def save(self, *args, **kwargs):

        newly_made = self.pk is None

        if self.reblog_of == self:
            raise ValueError("Status can't be a reblog of itself")

        if self.in_reply_to == self:
            raise ValueError("Status can't be a reply to itself")

        super().save(*args, **kwargs)

        if newly_made:
            trilby_signals.posted.send(sender=self)

    def __str__(self):
        return '[Status %s: %s]' % (
                self.id,
                self.content,
                )

    @classmethod
    def lookup(cls, url):

        # TODO: not yet tested
        # FIXME: if url is local, parse and return local <-- current breakage XXX
        # FIXME: if remote is not found, *possibly* create and return?

        if is_local(url):

            view = trilby_utils.find_local_view(
                    url,
                    )

            view = trilby_utils.find_local_view(
                    url,
                    which_views = ['StatusView'],
                    )

            if view is None:
                return None

            statusid = int(view.kwargs['status'])

            try:
                result = cls.objects.get(
                        id=statusid,
                        )
            except cls.DoesNotExist:
                logger.debug('%s is local but does not exist',
                        url)
                return None

            if result.account.local_user.username != view.kwargs['username']:
                logger.debug('%s is local but the username doesn\'t match',
                        url)
                return None

            logger.debug('%s is local and exists: %s',
                    url, result)
            return result

        # so, it's remote

        try:
            result = cls.objects.get(remote_url = url)
            logger.debug('%s is remote and exists: %s',
                    url, result)

            return result
        except cls.DoesNotExist:
            pass

        logger.debug('%s is unknown',
                url)

        return None

    @property
    def is_reply(self):
        return self.in_reply_to is not None

    @property
    def text(self):
        # XXX It's possible that one of (text, content) is
        # HTML and one is plain text. But the docs don't
        # seem to be forthcoming on this point, so we'll
        # just have to wait until we find out.
        return self.content

    @property
    def is_local(self):
        return self.remote_url is None
