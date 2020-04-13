from django.test import TestCase
from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

class TestStatus(TestCase):

    def _test_doing_something(self,
            verb, status):

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses/{}/{}'.format(
                    status.id,
                    verb,
                    ),
                format = 'json',
                )

        self.assertEqual(result.status_code,
                200)

    def test_publish_new(self):
        self.fail("Test not yet implemented")

    def test_view_specific_status(self):
        self.fail("Test not yet implemented")

    def test_delete_status(self):
        self.fail("Test not yet implemented")

    def test_get_context(self):
        self.fail("Test not yet implemented")

    def test_get_reblogged_by(self):
        self.fail("Test not yet implemented")

    def test_get_favourited_by(self):
        self.fail("Test not yet implemented")

    def test_favourite(self):

        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        self._test_doing_something('favourite',
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

    def test_unfavourite(self):

        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        self._test_doing_something('favourite',
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

        self._test_doing_something('unfavourite',
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 0,
                "There was no longer a Like object")

    def test_reblog(self):
        self.fail("Test not yet implemented")

    def test_unreblog(self):
        self.fail("Test not yet implemented")

    @skip("Not yet implemented")
    def test_bookmark(self):
        pass

    @skip("Not yet implemented")
    def test_unbookmark(self):
        pass

    @skip("Not yet implemented")
    def test_mute(self):
        pass

    @skip("Not yet implemented")
    def test_unmute(self):
        pass

    def test_pin(self):
        self.fail("Test not yet implemented")

    def test_unpin(self):
        self.fail("Test not yet implemented")
