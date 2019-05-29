from django.test import TestCase, Client
from . import *
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

        alice = create_local_person('alice')

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

        alice = create_local_person('alice')
        bob = create_local_person('bob')

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

class TestTombstone(TestCase):

    def test_tombstone(self):

        queen_anne = create_local_person('queen_anne')

        c = Client()
        response = c.get('/users/queen_anne')

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
                _response_to_dict(response),
                {
                    'name': 'queen_anne',
                    'id': 'https://altair.example.com/users/queen_anne',
                    'type': 'Person',
                    },
                )

        queen_anne.entomb()

        response = c.get('/users/queen_anne')

        self.assertEqual(response.status_code, 410)
        self.assertDictEqual(
                _response_to_dict(response),
                {
                    'id': 'https://altair.example.com/users/queen_anne',
                    'type': 'Tombstone',
                    'former_type': 'Person',
                    'name': 'queen_anne',
                    },
                )
