from django.db import models
from django_kepi import object_type_registry
from django_kepi.cache_model import Cache
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

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

