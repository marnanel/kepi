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

    @property
    def created_at(self):
        return self.actor.published

    @property
    def note(self):
        return self.actor.f_summary

    @property
    def display_name(self):
        return self.actor.f_name

    @property
    def locked(self):
        return False # TODO

    @property
    def moved_to(self):
        return None # TODO

    @property
    def linked_url(self):
        return None # TODO

    @property
    def default_visibility(self):
        return 'public' # FIXME

    @property
    def default_sensitive(self):
        return False # FIXME
