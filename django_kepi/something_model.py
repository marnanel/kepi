from django.db import models
from django_kepi import object_type_registry
from django_kepi.cache_model import Cache

#######################

class SomethingManager(models.Manager):

    f_type = None

    def get_queryset(self):
        # TODO augment QSs with contenttypes link to source

        result = models.QuerySet(
                model = self.parent_model,
                )

        handlers = [
            Cache.objects.filter(f_type=self.f_type),
            ]

        handlers.extend([
            h.objects.all()
            for h in object_type_registry[self.f_type]])

        return result

#######################

class Person(models.Model):

    f_type = 'Person'
    objects = SomethingManager()
    objects.f_type = f_type

    class Meta:
        managed = False

Person.objects.parent_model = Person # this is ugly

