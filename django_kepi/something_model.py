from django.db import models
from django_kepi import object_type_registry
from django_kepi.cache_model import Cache
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django_kepi.models import Thing
import logging

logger = logging.getLogger(name='django_kepi')

#######################

class ActivityModel(models.Model):
    def save(self, *args, **kwargs):

        we_are_new = self.pk is None

        super().save(*args, **kwargs)

        if we_are_new:
            logger.debug('New activity: %s',
                    str(self.activity_form))
            logger.debug('We must create a Create wrapper for it.')

            wrapper = Thing.create({
                'type': 'Create',
                'actor': self.activity_actor,
                'to': self.activity_to,
                'cc': self.activity_cc,
                'object': self.activity_id,
                })

            wrapper.save()
            logger.debug('Created wrapper %s',
                    str(wrapper.activity_form))

            # XXX We copy "to" and "cc" per
            # https://www.w3.org/TR/activitypub/#object-without-create
            # which also requires us to copy
            # the two blind versions, and "audience".
            # We don't support those (atm), but
            # we should probably copy them anyway.

    @property
    def activity_to(self):
        # FIXME
        return ["https://www.w3.org/ns/activitystreams#Public"]

    @property
    def activity_cc(self):
        # FIXME
        return ["https://marnanel.org/users/marnanel/followers"]
 
#######################

class SomethingManager(models.Manager):

    f_type = None

    def get_queryset(self):

        # This is an empty QuerySet; it's here because
        # it sets the type of the objects in the result.
        result = models.QuerySet(
                model = self.parent_model,
                )

        cache_query = Cache.objects.filter(f_type=self.f_type)
        cache_query.annotate(
                is_local = models.Value(
                    False
                    ),
                content_type = models.Value(
                    ContentType.objects.get_for_model(Cache),
                    ),
                )

        handlers = [
                cache_query,
            ]

        for h in object_type_registry[self.f_type]:
            query = h.objects.all()
            query.annotate(
                    is_local = models.Value(
                        True,
                        ),
                    content_type = models.Value(
                        ContentType.objects.get_for_model(h),
                        ),
                    )
            handlers.append(query)

        return result.union(*handlers)

#######################

class Person(models.Model):

    f_type = 'Person'
    objects = SomethingManager()
    objects.f_type = f_type

    content_type = models.ForeignKey(
            ContentType,
            on_delete=models.CASCADE,
            ),

    content_object = GenericForeignKey(
            'content_type',
            'url',
            ),

    class Meta:
        managed = False

Person.objects.parent_model = Person # this is ugly

