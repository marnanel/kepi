from django.db import models

object_type_registry = {
        'Object': None,
        }

def register_type(a_typename, a_typeclass):
    object_type_registry[a_typename] = a_typeclass

class ActivityObject(models.Model):
    a_type = models.CharField(max_length=255,
            default='Object')
    verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if self.a_type not in object_type_registry:
            raise ValueError("Can't save object with unknown type {}".format(
                self.a_type,
                ))

        super().save(*args, **kwargs)

    def activity_fields(self):

        result = {}

        try:
            a_typeclass = object_type_registry[self.a_type]
        except KeyError:
            raise ValueError("ActivityObject {} has unknown type {}".format(
                self.pk,
                self.a_type,
                ))

        if a_typeclass is not None:
            instance = a_typeclass.objects.find(activity_object__pk=self.pk)

            if instance is None:
                raise ValueError("ActivityObject {} has no corresponding instance in type {}".format(
                    self.pk,
                    self.a_type,
                    ))

            result.update(
                    instance.activity_fields(),
                    )

        result.update({
            'id': self.pk,
            'type': self.a_type,
            })

        return result
