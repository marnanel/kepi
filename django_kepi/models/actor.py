from django.db import models
import django_kepi.models.thing
import django_kepi.crypto
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Actor(models.Model):

    thing = models.OneToOneField(
            'django_kepi.Thing',
            primary_key=True,
            on_delete=models.CASCADE,
            )

    privateKey = models.TextField(
            )

    publicKey = models.TextField(
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

