from django.db import models
from django_kepi import register_type
from django_kepi.models import ActivityObject

class ThingUser(models.Model):

    name = models.CharField(max_length=256)
    activity_object = models.OneToOneField(
            ActivityObject,
            on_delete=models.CASCADE,
            )

    def activity_fields(self):
        return {
                'name': self.name,
                }

register_type('Person', ThingUser)

