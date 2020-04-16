from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for statuses. API docs are here:
# https://docs.joinmastodon.org/methods/statuses/

STATUS_EXPECTED = [
        ('in_reply_to_account_id', None),
        ('content', 'Hello world.'),
        ('emojis', []),
        ('reblogs_count', 0),
        ('favourites_count', 0),
        ('reblogged', False),
        ('favourited', False),
        ('muted', False),
        ('sensitive', False),
        ('spoiler_text', ''),
        ('visibility', 'A'),
        ('media_attachments', []),
        ('mentions', []),
        ('tags', []),
        ('card', None),
        ('poll', None),
        ('application', None),
        ('language', 'en'),
        ('pinned', False),
        ]

class TestStatus(TrilbyTestCase):

    def test_get_single_status(self):
        self._alice = create_local_person(name='alice')

        self._status = create_local_status(
                content = 'Hello world.',
                posted_by = self._alice,
                )

        request = self.factory.get(
                '/api/v1/statuses/'+str(self._status.id),
                )
        force_authenticate(request, user=self._alice.local_user)

        view = Statuses.as_view()

        result = view(request,
                id=str(self._status.id))

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content)

        # FIXME: Need to check that "id" corresponds to "url", etc

        for field, expected in STATUS_EXPECTED:
            self.assertIn(field, content)
            self.assertEqual(content[field], expected,
                    msg="field '{}'".format(field))

        self.assertIn('account', content)
        account = content['account']

        for field, expected in ACCOUNT_EXPECTED:
            self.assertIn(field, account)
            self.assertEqual(account[field], expected,
                    msg="account field '{}'".format(field))

        self.assertIn('id', content)
        try:
            dummy = int(content['id'])
        except ValueError:
            self.fail('Value of "id" is not a decimal: '+content['id'])


    def test_get_all_statuses(self):

        messages = [
                '<p>Why do I always dress myself in %s?</p>' % (colour,) \
                        for colour in ['red', 'green', 'blue', 'black']]

        self._create_alice()

        for message in messages:
            create_local_status(
                content = message,
                posted_by = self._alice,
                )

        request = self.factory.get(
                '/api/v1/statuses/',
                )
        force_authenticate(request, user=self._alice.local_user)

        view = Statuses.as_view()

        result = view(request)

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content)

        self.assertEqual(
                [x['content'] for x in content],
                messages,
                )

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

        result = self._test_doing_something('reblog',
                self._bob,
                self._alice_status)

        try:
            details = json.loads(result.content.decode('UTF-8'))
        except JSON.decoder.JSONDecodeError:
            self.fail("Response was not JSON")
            return

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
        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses/{}/reblog'.format(
                    1234,
                    ),
                )

        self.assertEqual(result.status_code,
                404)

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

    def test_get_status_context(self):

        self._create_alice()
        self._create_status()

        request = self.factory.get(
                '/api/v1/statuses/'+str(self._status.id)+'/context',
                )
        force_authenticate(request, user=self._alice.local_user)

        view = StatusContext.as_view()

        result = view(request,
                id=str(self._status.id))

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content)

        self.assertEqual(
                content,
                {
                    'ancestors': [],
                    'descendants': [],
                    })

    def test_get_emojis(self):
        request = self.factory.get(
                '/api/v1/emojis/',
                )

        view = Emojis.as_view()

        result = view(request)

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

    def test_post_status(self):

        self._create_alice()

        request = self.factory.post(
                '/api/v1/statuses/',
                {
                    'status': 'Hello world',
                    },
                format='json',
                )
        force_authenticate(request, user=self._alice.local_user)

        view = Statuses.as_view()

        result = view(request)

        self.assertEqual(
                result.status_code,
                200,
                'Result code',
                )

        content = json.loads(result.content.decode())

        self.assertEqual(
                content['content'],
                '<p>Hello world</p>',
                )

    @skip("serial numbers are not yet exposed")
    def test_post_multiple_statuses(self):

        self._create_alice()

        previous_serial = 0

        for i in range(0, 9):
            request = self.factory.post(
                    '/api/v1/statuses/',
                    {
                        'status': 'Hello world %d' % (i,),
                        },
                    format='json',
                    )
            force_authenticate(request, user=self._alice.local_user)

            view = Statuses.as_view()

            result = view(request)

            self.assertEqual(
                    result.status_code,
                    200,
                    'Result code',
                    )

            content = json.loads(result.content.decode())

            self.assertLess(
                    previous_serial,
                    content['serial'])

            previous_serial = content['serial']


class TestPublish(TrilbyTestCase):
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

class TestGetStatus(TrilbyTestCase):

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
            return

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
            return

        self.assertEqual(
                details['error'],
                'Record not found',
                )

