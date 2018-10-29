from django.db import models
from django_kepi import object_type_registry
from django_kepi.cache_model import Cache

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

        # XXX Trouble: this returns everything as a Cache,
        # whereas we want it to return a Person or whatever.
        # XXX Make a list and pass the whole list to union() once.
        # XXX Make a dummy first entry that returns zero Persons
        # (or whatever) so it gets the type right.
        for local_handler in object_type_registry[self.f_type]:
            print(local_handler)
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
