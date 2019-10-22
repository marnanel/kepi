from django.db import models
from django.db.models.signals import post_init
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from chapeau.kepi.models import AcPerson
from chapeau.kepi.create import create
from django.conf import settings
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
    def avatar(self):
        return self.actor.icon

    @property
    def header(self):
        return self.actor.header

    @property
    def locked(self):
        return False # TODO

    @property
    def moved_to(self):
        return None # TODO

    @property
    def url(self):
        return self.actor.url

    @property
    def fields(self):
        return [] # FIXME

    @property
    def emojis(self):
        return [] # FIXME

    @property
    def default_visibility(self):
        return 'public' # FIXME

    @property
    def default_sensitive(self):
        return False # FIXME

    @property
    def bot(self):
        return False # FIXME

    @property
    def language(self):
        return settings.KEPI['LANGUAGES'][0] # FIXME
