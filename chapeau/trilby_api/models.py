from django.db import models
from django.contrib.auth.models import AbstractUser
from chapeau.kepi.models import AcPerson

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
            on_delete=models.DO_NOTHING,
            unique=True,
            null=True,
            )


