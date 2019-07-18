from django.db import models
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
        return '%s#main-key' % (self.url,),

    @property
    def publicKey_as_dict(self):
        """
        A dict describing this Actor's public key,
        in the format used by ActivityStreams.

        The keys will be:
          'owner' - the url of this Actor
          'id'    - the name of the key
          'f_publicKeyPem' - the public key, in PEM format
                           (like, "----BEGIN PUBLIC KEY---" and so on)
        """

        result = {
                'id': self.key_name,
                'owner': self.url,
                'f_publicKeyPem': self.f_publicKey,
                }

        return result

    def __getitem__(self, name):
        if self.is_local:

            format_details = {
                    'username': self.f_preferredUsername,
                    }

            if name=='followers':
                return settings.KEPI['FOLLOWERS_PATH'] % format_details
            elif name=='following':
                return settings.KEPI['FOLLOWING_PATH'] % format_details
            elif name=='inbox':
                return settings.KEPI['INBOX_PATH'] % format_details
            elif name=='outbox':
                return settings.KEPI['OUTBOX_PATH'] % format_details

        if name=='f_publicKey':
            return self.f_publicKey_as_dict
        else:
            return super().__getitem__(name)
