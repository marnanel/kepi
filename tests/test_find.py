from django.test import TestCase
from django_kepi.find import find
from django_kepi.models import Thing, create
from django.conf import settings
from . import *
import httpretty
import json
import logging

logger = logging.getLogger(name='django_kepi')

REMOTE_URL = 'https://remote.example.net/fnord'

STUFF = {'a': 1, 'b': 2}

class TestFind(TestCase):

    @httpretty.activate
    def test_find_remote(self):

        mock_remote_object(
                REMOTE_URL,
                content = json.dumps(STUFF),
                )

        found = find(REMOTE_URL)

        self.assertDictEqual(
                found,
                STUFF,
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
            actor = 'https://example.net/users/fred',
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

        found = find(settings.KEPI['ACTIVITY_URL_FORMAT'] % ('walrus',) )

        self.assertIsNone(
                found,
                )

