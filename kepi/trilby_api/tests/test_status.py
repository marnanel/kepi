from django.test import TestCase
from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for statuses. API docs are here:
# https://docs.joinmastodon.org/methods/statuses/

class TestStatus(TestCase):

    def _test_doing_something(self,
            verb, person, status,
            expect_result = 200):

        c = APIClient()
        c.force_authenticate(person.local_user)

        result = c.post(
                '/api/v1/statuses/{}/{}'.format(
                    status.id,
                    verb,
                    ),
                format = 'json',
                )

        self.assertEqual(result.status_code,
                expect_result)

    def test_delete_status(self):

        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        found = Status.objects.filter(
                account = self._alice,
                )

        self.assertEqual(
                len(found),
                1,
                "There is a status.")

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.delete(
                '/api/v1/statuses/{}'.format(
                    self._alice_status.id,
                    ),
                )

        self.assertEqual(result.status_code,
                200)

        # TODO: result body is meaningful and we should check it

        found = Status.objects.filter(
                account = self._alice,
                )

        self.assertEqual(
                len(found),
                0,
                "There is no longer a status.")

    def test_delete_status_not_yours(self):

        self._alice = create_local_person(name='alice')
        self._eve = create_local_person(name='eve')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        c = APIClient()
        c.force_authenticate(self._eve.local_user)

        result = c.delete(
                '/api/v1/statuses/{}'.format(
                    self._alice_status.id,
                    ),
                )

        self.assertEqual(result.status_code,
                404)

    def test_delete_status_404(self):

        self._alice = create_local_person(name='alice')

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.delete(
                '/api/v1/statuses/{}'.format(
                    1234,
                    ),
                )

        self.assertEqual(result.status_code,
                404)

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

    def test_favourite_twice(self):

        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        self._test_doing_something('favourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

        self._test_doing_something('favourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "Likes are idempotent")

    def test_favourite_404(self):

        self._alice = create_local_person(name='alice')

        class Mock(object):
            def id():
                return 1234
        
        self._test_doing_something('favourite',
                self._alice,
                Mock(),
                expect_result = 404)

    def test_unfavourite(self):

        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        self._test_doing_something('favourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

        self._test_doing_something('unfavourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 0,
                "There was no longer a Like object")

    def test_unfavourite_twice(self):

        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        self._test_doing_something('favourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a Like object")

        self._test_doing_something('unfavourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 0,
                "There was no longer a Like object")

        self._test_doing_something('unfavourite',
                self._alice,
                self._alice_status)

        found = Like.objects.filter(
                liker = self._alice,
                liked = self._alice_status,
                )

        self.assertEqual(len(found), 0,
                "There was still no longer a Like object")

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


class TestPublish(TestCase):
    def test_publish_simple(self):

        self._alice = create_local_person(name='alice')

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses',
                {
                    'status': 'Hello world',
                    },
                format = 'json',
                )

        self.assertEqual(result.status_code,
                200)

        found = Status.objects.filter(
            account = self._alice,
                )

        self.assertEqual(len(found), 1,
                "The status was created")

class TestGetStatus(TestCase):

    def test_view_specific_status(self):
        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.get(
                '/api/v1/statuses/{}'.format(
                    self._alice_status.id,
                    ),
                )

        self.assertEqual(result.status_code,
                200)

        try:
            details = json.loads(result.content.decode('UTF-8'))
        except JSON.decoder.JSONDecodeError:
            self.fail("Response was not JSON")

        self.assertEqual(
                details['id'],
                str(self._alice_status.id),
                )

        self.assertEqual(
                details['account']['username'],
                'alice',
                )

        self.assertEqual(
                details['content'],
                'Daisies are our silver.',
                )

    def test_view_specific_status_404(self):
        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.get(
                '/api/v1/statuses/{}'.format(
                    self._alice_status.id+1234,
                    ),
                )

        self.assertEqual(result.status_code,
                404)

        try:
            details = json.loads(result.content.decode('UTF-8'))
        except JSON.decoder.JSONDecodeError:
            self.fail("Response was not JSON")

        self.assertEqual(
                details['error'],
                'Record not found',
                )

