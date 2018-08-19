from django.test import TestCase, Client
from django_kepi.models import Create
from things_for_testing.models import ThingUser
import json

class UserTests(TestCase):

    def test_basic_objects(self):

        actor = ThingUser(
                name='Fred',
                )
        actor.save()

        activity = Create(
                actor=actor,
                fobject=actor,
                )
        activity.save()

        raise ValueError(str(activity.serialize()))
