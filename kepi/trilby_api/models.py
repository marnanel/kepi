from django.db import models
from django.contrib.auth.models import AbstractUser
from kepi.bowler_pub.models import AcPerson, AcItem
from enum import Enum
from django.utils.timezone import now

class NotificationType(Enum):
    F = 'follow'
    M = 'mention'
    R = 'reblog'
    L = 'favourite'

class TrilbyUser(AbstractUser):

    actor = models.OneToOneField(
            AcPerson,
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
            AcPerson,
            on_delete = models.DO_NOTHING,
            )

    status = models.ForeignKey(
            AcItem,
            on_delete = models.DO_NOTHING,
            blank = True,
            null = True,
            )
