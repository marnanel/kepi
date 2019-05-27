from django.test import TestCase
from unittest import skip
from django_kepi.embellish import embellish
from . import *
import logging

logger = logging.getLogger(name='django_kepi')

@skip("Decide whether we're keeping this")
class TestEmbellish(TestCase):
    def test_embellish_note(self):

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

        user = create_person(
                name = 'Fred',
                url = 'https://example.com/users/fred',
                )

        result = embellish(SOURCE,
                user=user)

        self.maxDiff = None
        self.assertDictContainsSubset(
                EXPECTING,
                result,
                )

