from django.db import models
from django.conf import settings
from . import thing
import django_kepi.crypto
import logging

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

    def _after_create(self):
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

    @property
    def key_name(self):
        """
        The name of this key.
        """
        return '%s#main-key' % (self.url,)

    def list_path(self, name):
        return settings.KEPI['COLLECTION_PATH'] % {
                'username': self.f_preferredUsername,
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
