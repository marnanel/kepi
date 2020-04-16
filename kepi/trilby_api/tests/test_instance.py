from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for methods for the instance as a whole. API docs are here:
# https://docs.joinmastodon.org/methods/instance/

class TestInstance(TrilbyTestCase):

    def test_instance_query(self):
        result = self.get(
                '/api/v1/instance',
                )

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

    @skip("Not yet implemented")
    def test_list_peers(self):
        pass

    @skip("Not yet implemented")
    def test_list_weekly_activity(self):
        pass

    def test_get_emojis(self):
        result = self.get(
                '/api/v1/custom_emojis',
                )

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content.decode())

        self.assertEqual(
                content,
                [],
                )
