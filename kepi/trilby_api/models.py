from django.db import models
from django.contrib.auth.models import AbstractUser
from django.dispatch import receiver
import kepi.bowler_pub.models as kepi_models
import kepi.bowler_pub.signals as kepi_signals
import kepi.bowler_pub.find as kepi_find
from enum import Enum
from django.utils.timezone import now
import logging

logger = logging.Logger('kepi')

class NotificationType(Enum):
    F = 'follow'
    M = 'mention'
    R = 'reblog'
    L = 'favourite'

class TrilbyUser(AbstractUser):

    actor = models.OneToOneField(
            kepi_models.AcPerson,
            on_delete=models.CASCADE,
            unique=True,
            default=None,
            )

class Notification(models.Model):

    notification_type = models.CharField(
            max_length = 256,
            choices = [
                (tag, tag.value) for tag in NotificationType
                ],
            )

    created_at = models.DateTimeField(
            default = now,
            )

    account = models.ForeignKey(
            kepi_models.AcPerson,
            on_delete = models.DO_NOTHING,
            )

    status = models.ForeignKey(
            kepi_models.AcItem,
            on_delete = models.DO_NOTHING,
            blank = True,
            null = True,
            )

@receiver(kepi_signals.created)
def on_follow(sender, **kwargs):

    value = kwargs['value']

    if isinstance(value, kepi_models.AcFollow):

        logger.info('Storing a notification about this follow.')

        follower = kepi_find.find(value['object'])

        notification = Notification(
                notification_type = NotificationType.F,
                account = follower,
                )

        notification.save()
        logger.info('  -- notification is: %s',
                notification)
