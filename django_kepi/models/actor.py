from django.db import models
from django.conf import settings
from . import thing
import django_kepi.crypto
import logging
import json

logger = logging.getLogger(name='django_kepi')

######################

class Actor(thing.Object):
    """
    An Actor is a kind of Object representing a person,
    an organisation, a bot, or anything else that can
    post stuff and interact with other Actors.

    The most important thing about Actors specifically
    is that they own a public/private key pair.
    """

    privateKey = models.TextField(
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

    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return settings.KEPI['USER_URL_FORMAT'] % {
                'username': self.f_preferredUsername,
                'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                }

    def _after_create(self):
        if self.privateKey is None and self.f_publicKey is None:

            if not self.is_local:
                logger.warn('%s: Attempt to save remote without key',
                        self.url)
            else:
                logger.info('%s: generating key pair.',
                        self.url)

                key = django_kepi.crypto.Key()
                self.privateKey = key.private_as_pem()
                self.f_publicKey = key.public_as_pem()

    def __str__(self):
        if self.is_local:
            return 'local user {}'.format(self.f_preferredUsername)
        else:
            return 'remote user {}'.format(self.remote_url)

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

    def __setitem__(self, name, value):
        if name=='privateKey':
            self.privateKey = value
        elif name=='publicKey':
            self.f_publicKey = json.dumps(value,
                    sort_keys = True)
        else:
            super().__setitem__(name, value)

    def __getitem__(self, name):
        if self.is_local:

            if name in ('inbox', 'outbox',
                    'followers', 'following',
                    ):
                return self.list_path(name)
            elif name=='privateKey':
                return self.privateKey

        if name=='publicKey':
            return json.loads(self.f_publicKey)

        return super().__getitem__(name)

##############################

class Application(Actor):
    pass

class Group(Actor):
    pass

class Organization(Actor):
    pass

class Person(Actor):
    pass

class Service(Actor):
    pass
