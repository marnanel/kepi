from django.test import TestCase
from django_kepi.embellish import embellish
from things_for_testing.models import ThingUser
import logging

logger = logging.getLogger(name='django_kepi')

class TestEmbellish(TestCase):
    def test_embellish(self):

        SOURCE = {
                'id': 'https://example.com/users/fred/status/1234',
                'type': 'Note',
                'content': 'Hello world',
                }

        EXPECTING = {
                'id': 'https://example.com/users/fred/status/1234',
                'url': 'https://example.com/users/fred/status/1234',
                'atomUri': 'https://example.com/users/fred/status/1234',
                'type': 'Note',
                'content': 'Hello world',
                'summary': None,
                "attributedTo": "https://example.com/users/fred",
                "to":["https://www.w3.org/ns/activitystreams#Public"],
                "cc":["https://example.com/users/fred/followers"],
                "sensitive": False,
                "inReplyTo": None,
                "inReplyToAtomUri": None,
                "contentMap":{"en-us": 'Hello world',},
                "attachment":[],
                "tag":[],
                }
                # (plus "published")
                # (plus "conversation", wtf?)

        user = ThingUser(
                name = 'Fred',
                url = 'https://example.com/users/fred',
                )

        result = embellish(SOURCE,
                user=user)

        self.maxDiff = None
        self.assertDictContainsSubset(
                result,
                EXPECTING)

