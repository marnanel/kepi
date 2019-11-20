from django.db import models
from django.db.models.signals import post_init
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from kepi.bowler_pub.models import AcPerson
from kepi.bowler_pub.create import create
from django.conf import settings
import kepi.trilby_api.models

class TrilbyUser(AbstractUser):

    actor = models.OneToOneField(
            AcPerson,
            on_delete=models.CASCADE,
            unique=True,
            default=None,
            )
