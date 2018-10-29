from django.db import models
from django_kepi import object_type_registry
from django_kepi.cache_model import Cache
import json

#######################

class SomethingManager(models.Manager):

    f_type = None

    def get_queryset(self):
        # XXX Make sure all QSs return url
        # TODO augment QSs with contenttypes link to source
        result = Cache.objects.filter(
                f_type=self.f_type,
                )

        print(list(result))

        for local_handler in object_type_registry[self.f_type]:
            result = result.union(local_handler.objects.all())
            print(list(result))

        print('all')

        return result

#######################

class Person(models.Model):

    f_type = 'Person'
    objects = SomethingManager()
    objects.f_type = f_type

    class Meta:
        managed = False
