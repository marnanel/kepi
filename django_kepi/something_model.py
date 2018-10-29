from django.db import models
from django_kepi import object_type_registry

#######################

class Something(models.Model):

    f_type = 'Object'

    class Meta:
        abstract = True
        managed = False

    def get_queryset(self):

        result = Cache.objects.filter(
                f_type=self.f_type,
                )

        for local_handler in object_type_registry[self.f_type]:
            result = result.union(local_handler.objects)

        return result

#######################

class Person(models.Model):

    f_type = 'Person'

    class Meta:
        abstract = True
