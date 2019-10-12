from django.db import models
from django.contrib.auth.models import AbstractUser
from chapeau.kepi.models import AcPerson
from chapeau.kepi.create import create
import chapeau.trilby_api.models

def _create_actor(username):
    actor = {
            'id': '@'+username,
            'type': 'Person',
            }

    return create(
            value=actor,
            )

class TrilbyUser(AbstractUser):

    REQUIRED_FIELDS = ['username']
    # yes, the USERNAME_FIELD is the email, and not the username.
    # it's an oauth2 thing. just roll with it.
    USERNAME_FIELD = 'email'

    # We override "email" with a field that's almost identical,
    # but unique. This stops Django complaining that a non-unique
    # field is used for the username.

    email = models.EmailField(
            blank=True,
            unique=True,
            max_length=254,
            verbose_name='email address')

    actor = models.OneToOneField(
            AcPerson,
            on_delete=models.CASCADE,
            unique=True,
            default=None,
            )

    def save(self, *args, **kwargs):
        
        try:
            self.actor
        except TrilbyUser.actor.RelatedObjectDoesNotExist:
            self.actor = _create_actor(
                    username = self.username,
                    )

        super().save(*args, **kwargs)

    @property
    def acct(self):
        return self.actor.url

    def __getattr__(self, name):

        # If people look up an attribute which isn't on
        # this TrilbyUser, we pass it through to self.actor.
        # self.actor is always an AcObject, and these
        # allow lookup of arbitrary named values
        # using subscript.

        # If self.actor is None, we get AttributeError
        # anyway (because getattr on None always raises it).

        return self.actor[name]
