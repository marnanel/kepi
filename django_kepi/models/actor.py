from django.db import models
from django.conf import settings
from . import thing
import django_kepi.crypto
import logging
import json

logger = logging.getLogger(name='django_kepi')

######################

class Actor(thing.Thing):
    """
    An Actor is a kind of Thing representing a person,
    an organisation, a bot, or anything else that can
    post stuff and interact with other Actors.

    The most important thing about Actors specifically
    is that they own a public/private key pair.
    """

    # FIXME It's ludicrous to store some of these as JSON,
    # and it causes problems building queries downstream.

    f_privateKey = models.TextField(
            blank=True,
            null=True,
            )

    f_publicKey = models.TextField(
            blank=True,
            null=True,
            )

    auto_follow = models.BooleanField(
            default=True,
            )

    f_preferredUsername = models.CharField(
            max_length=255,
            )

    def save(self, *args, **kwargs):
        if self.f_privateKey is None and self.f_publicKey is None:

            if not self.is_local:
                logger.warn('%s: Attempt to save remote without key',
                        self.url)
            else:
                logger.info('%s: generating key pair.',
                        self.url)

                key = django_kepi.crypto.Key()
                self.f_privateKey = key.private_as_pem()
                self.f_publicKey = key.public_as_pem()

        super().save(*args, **kwargs)

    @property
    def key_name(self):
        """
        The name of this key.
        """
        return '%s#main-key' % (self.url,)

    def list_path(self, name):
        return settings.KEPI['COLLECTION_PATH'] % {
                'username': json.loads(self.f_preferredUsername),
                'listname': name,
                }

    @property
    def publicKey(self):
        result = self['publicKey']

    def __getitem__(self, name):
        if self.is_local:

            if name in ('inbox', 'outbox',
                    'followers', 'following',
                    ):
                return self.list_path(name)

        return super().__getitem__(name)
