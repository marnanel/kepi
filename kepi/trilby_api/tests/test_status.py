from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

class TestStatus(TestCase):

    def _create_alice(self):
        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

    def _test_doing_something(self,
            verb):

        self._create_alice()

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses/{}/{}'.format(
                    self._alice_status.id,
                    verb,
                    ),
                format = 'json',
                )

        self.assertEqual(result.status_code,
                200)

    def test_favourite(self):

        self._test_doing_something('favourite')

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

