from django.test import TestCase, Client
from django_kepi.models import *
from things_for_testing.models import ThingUser
from django_kepi import logger

class SomethingTests(TestCase):

    def add_to_cache(self, fields):
        result = Cache(
                url = fields['id'],
                f_type = fields['type'],
                fields = fields,
                )
        result.save()
        return result

    def test_cached(self):

        self.add_to_cache({
            'id': 'https://example.net/users/alice',
            'type': 'Person',
            'name': 'Alice Test',
            })

        alice = Person.objects.get(url='https://example.net/users/alice')

        self.assertEqual(alice.name, 'Alice Test')

    def test_local(self):

        thing = ThingUser(
                url = 'https://example.com/bob',
                name = 'Bob Test',
                favourite_colour = 'blue',
                )
        thing.save()

        bob = Person.objects.get(url='https://example.com/bob')
        self.assertEqual(bob.name, 'Bob Test')
