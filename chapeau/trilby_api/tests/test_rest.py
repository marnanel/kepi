from django.test import TestCase
from rest_framework.test import APIRequestFactory
from chapeau.trilby_api.views import *
import json

class TestRest(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

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
