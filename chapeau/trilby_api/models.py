from django.db import models
from django.db.models.signals import post_init
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from chapeau.kepi.models import AcPerson
from chapeau.kepi.create import create
import chapeau.trilby_api.models

class TrilbyUser(AbstractUser):

    actor = models.OneToOneField(
            AcPerson,
            on_delete=models.CASCADE,
            unique=True,
            default=None,
            )

    @property
    def acct(self):
        return self.actor.url

