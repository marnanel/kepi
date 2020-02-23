from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
import kepi.bowler_pub.models as bowler_pub_models
from django.conf import settings

class TestStatus(TestCase):

    def _create_alice(self):
        self._alice = create_local_trilbyuser(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

    def test_favourite(self):

        self._create_alice()

        c = APIClient()
        c.force_authenticate(self._alice)

        result = c.post(
                '/api/v1/statuses/{}/favourite'.format(
                    self._alice_status['object__obj'].serial,
                    ),
                format = 'json',
                )

        self.assertEqual(result.status_code,
                200)

        found = bowler_pub_models.AcLike.objects.filter(
                f_actor = self._alice,
                f_object = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

