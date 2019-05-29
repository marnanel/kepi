from django.db import models
import django_kepi.models.thing
import django_kepi.crypto
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Actor(models.Model):
    """
    An Actor is a kind of Thing representing a person,
    an organisation, a bot, or anything else that can
    post stuff and interact with other Actors.

    The most important thing about Actors specifically
    is that they own a public/private key pair.

    You can use your own actor class instead if you like,
    but you'll need to implement the same properties.
    """

    thing = models.OneToOneField(
            'django_kepi.Thing',
            primary_key=True,
            on_delete=models.CASCADE,
            )

    privateKey = models.TextField(
            )

    publicKey = models.TextField(
            )

    auto_follow = models.BooleanField(
            default=True,
            )

    @property
    def name(self):
        return self.thing.name

    def save(self, *args, **kwargs):
        if self.privateKey is None and self.publicKey is None:
            logger.info('Generating key pair for %s.',
                    self.name)
            
            key = django_kepi.crypto.Key()
            self.privateKey = key.private_as_pem()
            self.publicKey = key.public_as_pem()

        super().save(*args, **kwargs)

    @property
    def key_name(self):
        """
        The name of this key.
        """
        return '%s#main-key' % (self.thing.url,),

    @property
    def publicKey_as_dict(self):
        """
        A dict describing this Actor's public key,
        in the format used by ActivityStreams.

        The keys will be:
          'owner' - the url of this Actor
          'id'    - the name of the key
          'publicKeyPem' - the public key, in PEM format
                           (like, "----BEGIN PUBLIC KEY---" and so on)
        """

        result = {
                'id': self.key_name,
                'owner': self.thing.url,
                'publicKeyPem': self.publicKey,
                }

        return result

    def __getitem__(self, name):
        """
        Generally delegates to Thing.__getitem__(),
        except that 'publicKey' returns the value of
        publicKey_as_dict.
        """

        if name=='publicKey':
            return self.publicKey_as_dict
        else:
            return self.thing[name]

