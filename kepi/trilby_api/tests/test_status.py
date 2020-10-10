from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from kepi.bowler_pub.tests import create_remote_person
from kepi.bowler_pub.utils import uri_to_url
from django.conf import settings

# Tests for statuses. API docs are here:
# https://docs.joinmastodon.org/methods/statuses/

class TestStatus(TrilbyTestCase):

    def test_get_single_status(self):
        self._alice = create_local_person(name='alice')

        self._status = create_local_status(
                content = 'Hello world.',
                posted_by = self._alice,
                )

        content = self.get(
                path = '/api/v1/statuses/'+str(self._alice.id),
                as_user = self._alice,
                )

        for field, expected in STATUS_EXPECTED.items():
            self.assertIn(field, content)
            self.assertEqual(content[field], expected,
                    msg="field '{}'".format(field))

        self.assertIn('account', content)
        account = content['account']

        account_expected = ACCOUNT_EXPECTED.copy()
        account_expected['statuses_count'] = 1

        for field, expected in account_expected.items():

            if field.startswith('status['):
                # this doesn't give us the status dict
                continue

            self.assertIn(field, account)
            self.assertEqual(account[field], expected,
                    msg="account field '{}'".format(field))

        self.assertIn('id', content)

        self.assertIn('url', content)
        self.assertEqual(content['url'],
            uri_to_url(settings.KEPI['STATUS_LINK'] % {
                'username': 'alice',
                'id': content['id'],
                }))

    def _test_doing_something(self,
            verb, person, status,
            expect_result = 200):

        # This used to do a lot of the same work that self.post()
        # now does in the superclass. Now it just wraps self.post(),
        # because it gets called so often that it's not worth changing it.

        result = self.post(
                path='/api/v1/statuses/{}/{}'.format(
                    status.id,
                    verb,
                    ),
                as_user = person,
                expect_result = expect_result,
                )

        return result

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

        self._alice = create_local_person(name='alice')
        statuses = []

        previous = None

        for line in [
                'Daisies are our silver.',
                'Buttercups our gold.',
                'This is all the treasure',
                'We can have or hold.',
                'Raindrops are our diamonds.',
                'And the morning dew.',
                ]:
            statuses.append(create_local_status(
                posted_by = self._alice,
                content = line,
                in_reply_to = previous,
                ))

            previous = statuses[-1]

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.get(
                '/api/v1/statuses/{}/context'.format(
                    statuses[2].id,
                    ),
                )

        self.assertEqual(result.status_code,
                200)

        try:
            details = json.loads(result.content.decode('UTF-8'))
        except JSON.decoder.JSONDecodeError:
            self.fail("Response was not JSON")
            return

        self.assertEqual(
            sorted(details.keys()),
            ['ancestors', 'descendants'])

        self.assertEqual(len(details['ancestors']), 2)
        self.assertEqual(len(details['descendants']), 3)

        self.assertEqual(details['ancestors'][0]['id'],
            str(statuses[0].id))
        self.assertEqual(details['ancestors'][1]['id'],
            str(statuses[1].id))
        self.assertEqual(details['descendants'][0]['id'],
            str(statuses[3].id))
        self.assertEqual(details['descendants'][1]['id'],
            str(statuses[4].id))
        self.assertEqual(details['descendants'][2]['id'],
            str(statuses[5].id))

    def test_get_reblogged_by(self):
        self._alice = create_local_person(name='alice')
        self._bob = create_local_person(name='bob')
        self._carol = create_local_person(name='carol')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Look on my works, ye mighty, and despair.',
        )

        for fan in [self._bob, self._carol]:
            create_local_status(
                    posted_by = fan,
                    content = '',
                    reblog_of = self._alice_status,
                    )

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.get(
                '/api/v1/statuses/{}/reblogged_by'.format(
                    self._alice_status.id,
                    ),
                )

        self.assertEqual(result.status_code,
                200)

        try:
            details = json.loads(result.content.decode('UTF-8'))
        except JSON.decoder.JSONDecodeError:
            self.fail("Response was not JSON")
            return

        self.assertEqual(
                sorted([who['username'] for who in details]),
                ['bob', 'carol'],
                )

    def test_get_favourited_by(self):
        self._alice = create_local_person(name='alice')
        self._bob = create_local_person(name='bob')
        self._carol = create_local_person(name='carol')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Turkey trots to water.',
        )

        for fan in [self._bob, self._carol]:
            like = Like(
                    liker = fan,
                    liked = self._alice_status,
                    )
            like.save()

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.get(
                '/api/v1/statuses/{}/favourited_by'.format(
                    self._alice_status.id,
                    ),
                )

        self.assertEqual(result.status_code,
                200)

        try:
            details = json.loads(result.content.decode('UTF-8'))
        except JSON.decoder.JSONDecodeError:
            self.fail("Response was not JSON")
            return

        self.assertEqual(
                sorted([who['username'] for who in details]),
                ['bob', 'carol'],
                )

    def test_favourite(self):

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

    def test_reblog_status(self):

        self._alice = create_local_person(name='alice')
        self._bob = create_local_person(name='bob')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Casting down their golden crowns.',
        )

        details = self._test_doing_something('reblog',
                person = self._bob,
                status = self._alice_status)

        self.assertEqual(
                details['account']['username'],
                'bob',
                )

        self.assertEqual(
                details['reblog']['id'],
                str(self._alice_status.id),
                )

    def test_reblog_status_404(self):
        self._alice = create_local_person(name='alice')

        result = self.post(
                '/api/v1/statuses/{}/reblog'.format(
                    1234,
                    ),
                as_user = self._alice,
                expect_result = 404,
                )

    def test_unreblog_status(self):
        self._alice = create_local_person(name='alice')
        self._bob = create_local_person(name='bob')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Among the leaves so green, oh.',
        )

        self._bob_reblog = create_local_status(
                posted_by = self._bob,
                content = '',
                reblog_of = self._alice_status,
        )

        found = Status.objects.filter(
                reblog_of = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a reblog")

        self._test_doing_something('unreblog',
                self._bob,
                self._alice_status)

        found = Status.objects.filter(
                reblog_of = self._alice_status,
                )

        self.assertEqual(len(found), 0,
                "There was no longer a reblog")

    def test_unreblog_status_404(self):
        self._alice = create_local_person(name='alice')
        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses/{}/unreblog'.format(
                    1234,
                    ),
                )

        self.assertEqual(result.status_code,
                404)

    def test_unreblog_status_not_yours(self):
        self._alice = create_local_person(name='alice')
        self._bob = create_local_person(name='bob')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Among the leaves so green, oh.',
        )

        self._bob_reblog = create_local_status(
                posted_by = self._bob,
                content = '',
                reblog_of = self._alice_status,
        )

        found = Status.objects.filter(
                reblog_of = self._alice_status,
                )

        self.assertEqual(len(found), 1,
                "There was a reblog")

        response = self._test_doing_something('unreblog',
                self._alice,
                self._alice_status,
                expect_result = 404)

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

    @skip("Not yet implemented")
    def test_pin(self):
        self.fail("Test not yet implemented")

    @skip("Not yet implemented")
    def test_unpin(self):
        self.fail("Test not yet implemented")

    def test_post_status(self):

        self._create_alice()

        content = self.post(
                path = '/api/v1/statuses',
                data = {
                    'status': 'Hello world',
                    },
                as_user = self._alice,
                )

        self.assertEqual(
                content['content'],
                '<p>Hello world</p>',
                )

class TestPublish(TrilbyTestCase):
    def test_publish_simple(self):

        self._alice = create_local_person(name='alice')

        self.post(
                '/api/v1/statuses',
                {
                    'status': 'Hello world',
                    },
                as_user = self._alice,
                )

        found = Status.objects.filter(
            account = self._alice,
                )

        self.assertEqual(len(found), 1,
                "The status was created")

class TestGetStatus(TrilbyTestCase):

    def test_view_specific_status(self):
        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        details = self.get(
                '/api/v1/statuses/{}'.format(
                    self._alice_status.id,
                    ),
                as_user = self._alice,
                expect_result = 200,
                )

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
                '<p>Daisies are our silver.</p>',
                )

    def test_view_specific_status_404(self):
        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        details = self.get(
                path='/api/v1/statuses/{}'.format(
                    self._alice_status.id+1234,
                    ),
                expect_result = 404,
                )

        self.assertEqual(
                details['detail'],
                'Not found.',
                )

    def test_is_local(self):
        self._alice = create_local_person(name='alice')

        self._alice_status = create_local_status(
                posted_by = self._alice,
                content = 'Daisies are our silver.',
        )

        self.assertTrue(
                self._alice_status.is_local,
                )

        self._bob = create_remote_person(
                url = "https://example.org/people/bob",
                name='bob',
                auto_fetch = True,
                )

        self._bob_status = Status(
                remote_url = "https://example.org/people/bob/status/100",
                account = self._bob,
                in_reply_to = self._alice_status,
                content = "Buttercups our gold.",
                )
        self._bob_status.save()

        self.assertFalse(
                self._bob_status.is_local,
                )
