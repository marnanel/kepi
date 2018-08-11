from django.db import models

object_type_registry = {
        'Object': None,
        }

def register_type(type_name, type_class):
    object_type_registry[type_name] = type_class

class ActivityObject(models.Model):
    type_ = models.CharField(max_length=255,
            default='Object')
    verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):

        if self.type_ not in object_type_registry:
            raise ValueError("Can't save object with unknown type {}".format(
                self.type_,
                ))

        super().save(*args, **kwargs)

    def activity_fields(self):

        result = {}

        try:
            type_class = object_type_registry[self.type_]
        except KeyError:
            raise ValueError("ActivityObject {} has unknown type {}".format(
                self.pk,
                self.type_,
                ))

        if type_class is not None:
            instance = type_class.objects.find(activity_object__pk=self.pk)

            if instance is None:
                raise ValueError("ActivityObject {} has no corresponding instance in type {}".format(
                    self.pk,
                    self.type_,
                    ))

            result.update(
                    instance.activity_fields(),
                    )

        result.update({
            'id': self.pk,
            'type': self.type_,
            })

        return result
