from django.test import TestCase, Client
from django_kepi.models import Create
import json

class UserTests(TestCase):

    def test_basic_objects(self):

        c = Create()
        c.save()

