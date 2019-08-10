from django.test import TestCase
from django_kepi.find import find
from django_kepi.create import create
from django.conf import settings
from . import *
import httpretty
import json
import logging

logger = logging.getLogger(name='django_kepi')

REMOTE_URL = 'https://remote.example.net/fnord'

STUFF = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": REMOTE_URL,
        "type": "Note",
        "to": ["https://altair.example.com/someone"],
        "attributedTo": "https://europa.example.org/someone-else",
        "content": "I've got a lovely bunch of coconuts.",
    }

class TestFind(TestCase):

    def _mock_remote_stuff(self):
        mock_remote_object(
                REMOTE_URL,
                content = json.dumps(STUFF),
                )

    @httpretty.activate
    def test_find_remote(self):

        self._mock_remote_stuff()

        found = find(REMOTE_URL)

        self.assertEqual(
                found.url,
                REMOTE_URL)

        self.assertFalse(
                found.is_local,
                )

        self.assertDictContainsSubset(
                {
                    'attributedTo': 'https://europa.example.org/someone-else',
                    'id': 'https://remote.example.net/fnord',
                    'to': ['https://altair.example.com/someone'],
                    'type': 'Note'},
                found.activity_form,
                )

    @httpretty.activate
    def test_find_remote_404(self):

        mock_remote_object(
                REMOTE_URL,
                content = '',
                )

        found = find(REMOTE_URL)

        self.assertIsNone(found)

    def test_find_local(self):

        a = create(
            f_actor = 'https://example.net/users/fred',
            f_object = 'https://example.net/articles/i-like-jam',
            f_type = 'Like',
            )
        a.save()
        
        found = find(a.url)

        self.assertDictEqual(
                found.activity_form,
                a.activity_form,
                )

    def test_find_local_404(self):

        found = find(settings.KEPI['ACTIVITY_URL_FORMAT'] % {
            'number': 'walrus',
            'hostname': 'altair.example.com',
            })

        self.assertIsNone(
                found,
                )

