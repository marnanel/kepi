from django.test import TestCase, Client
from django_kepi.models import *
from things_for_testing.models import ThingUser
import json
from django_kepi import logger

class SomethingTests(TestCase):

    def add_to_cache(self, fields):
        text = json.dumps(fields)
        result = Cache(
                url = fields['id'],
                f_type = fields['type'],
                value = text,
                )
        result.save()
        return result

    def check_simple(self):

        self.add_to_cache({
            'id': 'https://example.net/users/alice',
            'type': 'Person',
            'name': 'Alice Test',
            })
