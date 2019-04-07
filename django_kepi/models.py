from django.db import models
from django_kepi import object_type_registry, find, register_type, logger
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import django_kepi.tasks
import logging
import random
import json
import datetime
import warnings
import uuid

from django_kepi.activity_model import *
from django_kepi.cache_model import *
from django_kepi.something_model import *
from django_kepi.validation import *

#######################

class CachedText(models.Model):

    key = models.UUIDField(
            primary_key = True,
            default = uuid.uuid4,
            )

    source = models.URLField(
            )

    contents = models.TextField(
            default = None,
            null = True,
            )

    # FIXME expiry datetime

#######################

class QuarantinedMessage(models.Model):

    username = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            default=None)

    headers = models.TextField()
    body = models.TextField()

    signature_verified = models.BooleanField(
            default=False,
            )

    def deploy(self,
            retrying=False):

        if retrying:
            logger.debug('%s: re-attempting to deploy', self)

            remaining_qmns = QuarantinedMessageNeeds.objects.filter(
                    message=self.pk,
                    )
            
            if remaining_qmns.exists():
                logger.debug('%s:  -- but there are dependencies remaining: %s',
                        self, remaining_qmns)
                return None
        else:
            logger.debug('%s: attempting to deploy', self)

        try:
            value = json.loads(self.body)
        except json.decoder.JSONDecodeError:
            logger.info('%s: JSON was invalid; deleting', self)
            self.delete()
            return None

        activity = Activity.create(
                    value = value,
                    from_message = self,
                    )
    
        if activity is None:
            logger.debug('%s: deployment failed because dependencies remain',
                    self)

            if retrying:
                logger.error("%s: dependencies remaining when all dependency records were gone; this should never happen")
                raise RuntimeError("dependencies remaining on retry")
               
            return None
        else:
            logger.info('%s: deployment was successful', self)
            self.delete()

        return activity

    def __str__(self):
        return 'QM{}'.format(self.pk)

class QuarantinedMessageNeeds(models.Model):

    class Meta:
        index_together = ["message", "needs_to_fetch"]

    id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
            )

    message = models.ForeignKey(QuarantinedMessage,
            on_delete=models.CASCADE)

    # TODO: add indexing when we have tests working

    needs_to_fetch = models.URLField()

    def start_looking(self):
        django_kepi.tasks.fetch.delay(
                fetch_url = self.needs_to_fetch,
                post_data = None,
                result_url = 'https://localhost/async_result', # XXX
                result_id = self.id,
                )

    def __str__(self):
        return 'QM{} needs {}'.format(
                self.message.pk,
                self.needs_to_fetch,
                )

#######################

__all__ = [
        'Activity',
        'Cache',
        'Person',
        'QuarantinedMessage',
        'QuarantinedMessageNeeds',
        'new_activity_identifier',
        ]
