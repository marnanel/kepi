from django.test import TestCase, Client
from . import _create_person
import logging
import json

logger = logging.getLogger(name='django_kepi')

def _response_to_dict(response):

    result = json.loads(response.content.decode('utf-8'))

    # @context is often huge, and is irrelevant for testing here
    if '@context' in result:
        del result['@context']

    logger.info('Response: %s', result)

    return result

class TestKepiView(TestCase):

    def test_single_kepi_view(self):

        alice = _create_person('alice')

        c = Client()
        response = c.get('/users/alice')
        result = _response_to_dict(response)

        self.assertDictEqual(
                result,
                {
                    'name': 'alice',
                    'id': 'https://altair.example.com/users/alice',
                    'type': 'Person',
                    },
                )

    def test_multiple_kepi_view(self):

        alice = _create_person('alice')
        bob = _create_person('bob')

        c = Client()
        response = c.get('/users')
        result = _response_to_dict(response)

        self.assertDictEqual(
                result,
                {
                    "first": "http://testserver/users?page=1",
                    "id": "http://testserver/users",
                    "totalItems": 2,
                    "type": "OrderedCollection"
                    }
                )

        response = c.get('/users?page=1')
        result = _response_to_dict(response)

        self.assertDictEqual(
                result,
                {
                    'id': 'http://testserver/users?page=1',
                    'orderedItems': [
                        { 'id': 'https://altair.example.com/users/alice',
                            'name': 'alice',
                            'type': 'Person',
                            },
                        { 'id': 'https://altair.example.com/users/bob',
                            'name': 'bob',
                            'type': 'Person',
                            }
                        ],
                    'partOf': 'http://testserver/users',
                    'totalItems': 2,
                    'type': 'OrderedCollectionPage',
                    }
                )

