from django.conf import settings
from django.test import TestCase, Client
from kepi.trilby_api.tests import create_local_person
import logging
import json

WEBFINGER_BASE_URL = 'https://altair.example.com/.well-known/webfinger'
WEBFINGER_URL = WEBFINGER_BASE_URL + '?resource={}'
WEBFINGER_MIME_TYPE = 'application/jrd+json; charset=utf-8'

logger = logging.getLogger(name='kepi')

class TestWebfinger(TestCase):

    def setUp(self):
        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))

        create_local_person(
                name='alice',
                publicKey=keys['public'],
                privateKey=keys['private'],
                )

        self._alice_keys = keys

        settings.ALLOWED_HOSTS = [
                'altair.example.com',
                'testserver',
                ]

        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def _fetch(self, url):
        client = Client()
        response = client.get(
                url,
                HTTP_ACCEPT = WEBFINGER_MIME_TYPE,
                )
        return response

    def test_no_resource(self):
        response = self._fetch(
                url=WEBFINGER_BASE_URL,
                )

        self.assertEqual(response.status_code, 400)

    def test_malformed(self):
        response = self._fetch(
                url=WEBFINGER_URL.format(
                    'I like coffee',
                    ),
                )

        self.assertEqual(response.status_code, 404)

    def test_wrong_server(self):
        response = self._fetch(
                url=WEBFINGER_URL.format(
                    'jamie@magic-torch.example.net',
                    ),
                )

        self.assertEqual(response.status_code, 404)

    def test_unknown_user(self):
        response = self._fetch(
                url=WEBFINGER_URL.format(
                    'lord_lucan@altair.example.com',
                    ),
                )

        self.assertEqual(response.status_code, 404)

    def test_working(self):

        response = self._fetch(
                url=WEBFINGER_URL.format(
                    'alice@testserver',
                    ),
                )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'],
                WEBFINGER_MIME_TYPE)

        # per RFC:
        self.assertEqual(response['Access-Control-Allow-Origin'],
            '*')

        parsed = json.loads(response.content)

        self.assertEqual(parsed['subject'],
            'acct:alice@testserver',
            )

        self.assertIn(
            'https://testserver/users/alice',
            parsed['aliases'],
            )

        self.assertIn(
                {
                    'rel': 'self',
                    'type': 'application/activity+json',
                    'href': 'https://testserver/users/alice',
                    },
                parsed['links'],
                )
