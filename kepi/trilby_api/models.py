from django.db import models
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
from django.conf import settings
import kepi.bowler_pub.models as kepi_models
import kepi.bowler_pub.signals as kepi_signals
import kepi.bowler_pub.find as kepi_find
from kepi.bowler_pub.create import create
import kepi.bowler_pub.crypto as crypto
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

    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return settings.KEPI['USER_LINK'] % {
                'username': self.local_user.username,
                }

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
        return 'FIXME' # FIXME

    @property
    def username(self):
        if self.remote_url is not None:
            return self.remote_username
        else:
            return self.local_user.username

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

###################

class Status(models.Model):

    # TODO: The original design has the serial number
    # monotonically but unpredictably increasing.

    @property
    def url(self):
        return 'FIXME' # FIXME

    @property
    def uri(self):
        return 'FIXME' # FIXME

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
            )

    spoiler_text = models.CharField(
            max_length = 255,
            )

    visibility = models.CharField(
            max_length = 255,
            )

    language = models.CharField(
            max_length = 255,
            )

    idempotency_key = models.CharField(
            max_length = 255,
            )

###################

class Notification(models.Model):

    FOLLOW = 'F'
    MENTION = 'M'
    REBLOG = 'R'
    FAVOURITE = 'L'

    TYPE_CHOICES = [
            (FOLLOW, 'follow'),
            (MENTION, 'mention'),
            (REBLOG, 'reblog'),
            (FAVOURITE, 'favourite'),
            ]

    notification_type = models.CharField(
            max_length = 256,
            choices = TYPE_CHOICES,
            )

    created_at = models.DateTimeField(
            default = now,
            )

    for_account = models.ForeignKey(
            TrilbyUser,
            on_delete = models.DO_NOTHING,
            )

    about_account = models.CharField(
            max_length = 256,
            default='',
            )

    status = models.ForeignKey(
            kepi_models.AcItem,
            on_delete = models.DO_NOTHING,
            blank = True,
            null = True,
            )

    @property
    def about_account_actor(self):
        return kepi_models.AcActor.get_by_url(self.about_account)

    def __str__(self):

        if self.notification_type == self.FOLLOW:
            detail = '%s has followed you' % (self.about_account,)
        elif self.notification_type == self.MENTION:
            detail = '%s has mentioned you' % (self.about_account,)
        elif self.notification_type == self.REBLOG:
            detail = '%s has reblogged you' % (self.about_account,)
        elif self.notification_type == self.FAVOURITE:
            detail = '%s has favourited your status' % (self.about_account,)
        else:
            detail = '(%s?)' % (self.notification_type,)

        return '[%s: %s]' % (
                self.for_account.id,
                detail,
                )

##################################################
# Notification handlers

# FIXME these are really similar. Can we refactor?

@receiver(kepi_signals.created)
def on_follow(sender, **kwargs):

    value = kwargs['value']

    if isinstance(value, kepi_models.AcFollow):

        follower_acperson = kepi_find.find(
                value['object'],
                local_only = True,
                )

        if follower_acperson is None:
            logger.info('  -- not storing a notification, because '+\
                    'nobody\'s being followed')
            return

        try:
            follower = TrilbyUser.objects.get(actor=follower_acperson)
        except TrilbyUser.DoesNotExist:
            logger.info('  -- not storing a notification, because '+\
                    'we don\'t know the person being followed')
            return

        logger.info('  -- storing a notification about this follow')

        following = value['actor']

        notification = Notification(
                notification_type = Notification.FOLLOW,
                for_account = follower,
                about_account = following,
                )

        notification.save()

        logger.info('      -- notification is: %s',
                notification)

@receiver(kepi_signals.created)
def on_like(sender, **kwargs):

    value = kwargs['value']

    if isinstance(value, kepi_models.AcLike):

        status = kepi_find.find(
                value['object'],
                local_only = True)

        if status is None:
            logger.info('  -- not storing a notification, because '+\
                    "there's no local object")
            return

        owner_acperson = status['attributedTo__obj']

        if owner_acperson is None:
            logger.info('  -- not storing a notification, because '+\
                    'there\'s no owner')
            return

        try:
            owner = TrilbyUser.objects.get(actor=owner_acperson)
        except TrilbyUser.DoesNotExist:
            logger.info('  -- not storing a notification, because '+\
                    'we don\'t know the owner')
            return

        logger.info('  -- storing a notification about this like')

        sender = value['actor']

        notification = Notification(
                notification_type = Notification.FAVOURITE,
                for_account = owner,
                about_account = sender,
                status = status,
                )

        notification.save()

        logger.info('      -- notification is: %s',
                notification)
