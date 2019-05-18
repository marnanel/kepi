from django.test import TestCase
from django_kepi.find import find
from django_kepi.activity_model import Thing
from django.conf import settings
from things_for_testing import KepiTestCase
import httpretty
import json

REMOTE_URL = 'https://remote.example.net/fnord'

STUFF = {'a': 1, 'b': 2}

class TestFind(KepiTestCase):

    @httpretty.activate
    def test_find_remote(self):

        self._mock_remote_object(
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

        self._mock_remote_object(
                REMOTE_URL,
                content = '',
                )

        found = find(REMOTE_URL)

        self.assertIsNone(found)

    def test_find_local(self):

        a = Thing(
                f_actor = 'https://example.net/users/fred',
                f_object = 'https://example.net/articles/i-like-jam',
                f_type = 'L',
                )
        a.save()
        
        found = find(a.url)

        self.assertDictEqual(
                found,
                a.activity_form,
                )

    def test_find_local_404(self):

        found = find(settings.KEPI['ACTIVITY_URL_FORMAT'] % ('walrus',) )

        self.assertIsNone(
                found,
                )

