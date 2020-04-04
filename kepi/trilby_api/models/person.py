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

class TrilbyUser(AbstractUser):
    """
    A Django user.
    """
    pass

class Person(models.Model):

    remote_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            unique = True,
            )

    remote_username = models.CharField(
            max_length = 255,
            null = True,
            blank = True,
            )

    local_user = models.OneToOneField(
            to = TrilbyUser,
            on_delete = models.CASCADE,
            null = True,
            blank = True,
            )

    icon_image = models.ImageField(
            help_text="A small square image used to identify you.",
            null=True,
            verbose_name='icon',
            )

    header_image = models.ImageField(
            help_text="A large image, wider than it's tall, which appears "+\
                    "at the top of your profile page.",
            null=True,
            verbose_name='header image',
            )

    @property
    def icon_or_default(self):
        if self.icon_image:
            return self.icon_image

        which = self.id % 10
        return uri_to_url('/static/defaults/avatar_{}.jpg'.format(
            which,
            ))

    @property
    def header_or_default(self):
        if self.header_image:
            return self.header_image

        return uri_to_url('/static/defaults/header.jpg')

    display_name = models.TextField(
            verbose_name='display name',
            help_text = 'Your name, in human-friendly form. '+\
                'Something like "Alice Liddell".',
            )

    created_at = models.DateTimeField(
            default = now,
            )

    publicKey = models.TextField(
            blank=True,
            null=True,
            verbose_name='public key',
            )

    privateKey = models.TextField(
            blank=True,
            null=True,
            verbose_name='private key',
            )

    note = models.TextField(
            max_length=255,
            help_text="Your biography. Something like "+\
                    '"I enjoy falling down rabbitholes."',
            default='',
            verbose_name='bio',
            )

    auto_follow = models.BooleanField(
            default=True,
            help_text="If True, follow requests will be accepted automatically.",
            )

    locked = models.BooleanField(
            default=False,
            help_text="If True, only followers can see this account's statuses.",
            )

    bot = models.BooleanField(
            default=False,
            help_text="If True, this account is a bot. If False, it's a human.",
            )

    moved_to = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = True,
            help_text="If set, this account has moved away, and "+\
                    "this is where it went."
            )

    default_visibility = models.CharField(
            max_length = 255,
            default = 'public',
            )

    default_sensitive = models.BooleanField(
            default = False,
            )

    language = models.CharField(
            max_length = 255,
            null = True,
            default = settings.KEPI['LANGUAGES'][0],
            )

    @property
    def uri(self):
        if self.remote_url is not None:
            return self.remote_url

        return settings.KEPI['USER_LINK'] % {
                'username': self.local_user.username,
                }
    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return uri_to_url(settings.KEPI['USER_LINK'] % {
                'username': self.local_user.username,
                })

    @property
    def following_count(self):
        return 0 # FIXME

    @property
    def followers_count(self):
        return 0 # FIXME

    @property
    def statuses_count(self):
        return 0 # FIXME

    @property
    def acct(self):
        if self.remote_url is not None:
            return self.remote_username
        else:
            return '{}@{}'.format(
                    self.local_user.username,
                    settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                    )

    @property
    def username(self):
        if self.remote_url is not None:
            return self.remote_username
        else:
            return self.local_user.username

    @property
    def api_id(self):
        if self.remote_url is not None:
            return self.remote_url
        else:
            return '@' + self.local_user.username

    def _generate_keys(self):

        logger.info('%s: generating key pair.',
                self.url)

        key = crypto.Key()
        self.privateKey = key.private_as_pem()
        self.publicKey = key.public_as_pem()

    def save(self, *args, **kwargs):
        
        # Validate: either remote or local but not both or neither.
        remote_set = \
                self.remote_url is not None and \
                self.remote_username is not None

        local_set = \
                self.local_user is not None

        if local_set == remote_set:
            raise ValidationError(
                    "Either local or remote fields must be set."
                    )

        # Create keys, if we're local and we don't have them.

        if local_set and self.privateKey is None and self.publicKey is None:
            self._generate_keys()

        # All good.

        super().save(*args, **kwargs)

    @property
    def followers(self):
        return None # FIXME

    @property
    def following(self):
        return None # FIXME

    @property
    def fields(self):
        return [] # FIXME

    @property
    def emojis(self):
        return [] # FIXME

    @property
    def inbox(self):

        import kepi.trilby_api.models as trilby_models

        def inbox_generator():
            for status in trilby_models.Status.objects.all():
                yield status

        return inbox_generator()

    @property
    def outbox(self):
        return [] # FIXME

    def __str__(self):
        if self.remote_url:
            return self.remote_url
        else:
            return self.local_user
