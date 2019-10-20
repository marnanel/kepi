from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from chapeau.trilby_api.views import *
from chapeau.trilby_api.tests import create_local_trilbyuser
from django.conf import settings
import json

ACCOUNT_EXPECTED = [
        ('id', 'alice'),
        ('username', 'alice'),
        ('acct', 'https://testserver/users/alice'),
        ('display_name', 'alice'),
        ('locked', False),

        ('followers_count', 0),
        ('following_count', 0),
        ('statuses_count', 0),
        ('note', ''),
        ('url', 'https://testserver/users/alice'),
        ('fields', []),
        ('emojis', []),

        ('bot', False),
        ]

ACCOUNT_SOURCE_EXPECTED = [
        ('privacy', 'default'),
        ('sensitive', False),
        ('language', 'en'),
        ]

class TestRest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def test_instance(self):
        request = self.factory.get(
                '/api/v1/instance',
                )
        view = Instance.as_view()

        result = view(request)

        self.assertEqual(
                result.status_code,
                200,
                )

        content = json.loads(result.content)

        for k in [
                "uri", "title", "description",
                "email", "version",
                "urls", "languages", "contact_account",
                ]:
            self.assertIn(k, content)

    def test_verify_credentials_anonymous(self):
        request = self.factory.get(
                '/api/v1/accounts/verify_credentials',
                )
        view = Verify_Credentials.as_view()

        result = view(request)

        self.assertEqual(
                result.status_code,
                401,
                )

    def test_verify_credentials(self):

        alice = create_local_trilbyuser(name='alice')

        request = self.factory.get(
                '/api/v1/accounts/verify_credentials',
                )
        force_authenticate(request, user=alice)

        view = Verify_Credentials.as_view()

        result = view(request)

        self.assertEqual(
                result.status_code,
                200,
                )

        content = json.loads(result.content)

        self.assertIn('created_at', content)
        self.assertNotIn('email', content)

        for field, expected in ACCOUNT_EXPECTED:
            self.assertIn(field, content)
            self.assertEqual(content[field], expected)

        self.assertIn('source', content)

        for field, expected in ACCOUNT_SOURCE_EXPECTED:
            self.assertIn(field, content['source'])
            self.assertEqual(content['source'][field], expected)
