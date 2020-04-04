from django.test import TestCase
from rest_framework.test import force_authenticate, APIClient, APIRequestFactory
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from django.conf import settings
from unittest import skip
import json

ACCOUNT_EXPECTED = [
        ('id', '@alice'),
        ('username', 'alice'),
        ('acct', 'alice@testserver'),
        ('display_name', 'alice'),
        ('locked', False),

        ('followers_count', 0),
        ('following_count', 0),
        ('statuses_count', 0),
        ('note', ''),
        ('url', 'https://testserver/users/alice'),
        ('fields', []),
        ('emojis', []),

        ('avatar', 'https://testserver/static/defaults/avatar_1.jpg'),
        ('header', 'https://testserver/static/defaults/header.jpg'),
        ('avatar_static', 'https://testserver/static/defaults/avatar_1.jpg'),
        ('header_static', 'https://testserver/static/defaults/header.jpg'),

        ('bot', False),
        ]

ACCOUNT_SOURCE_EXPECTED = [
        ('privacy', 'A'),
        ('sensitive', False),
        ('language', settings.KEPI['LANGUAGES'][0]), # FIXME
        ]

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
        self._user_test(
                name='verify_credentials',
                )

    def test_user(self):
        self._user_test(
                name='alice',
                )

    def _user_test(self, name):
        alice = create_local_person(name='alice')

        request = self.factory.get(
                '/api/v1/accounts/'+name,
                )
        force_authenticate(request, user=alice.local_user)

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
            self.assertEqual(content[field], expected,
                    msg="field '{}'".format(field))

        self.assertIn('source', content)

        for field, expected in ACCOUNT_SOURCE_EXPECTED:
            self.assertIn(field, content['source'])
            self.assertEqual(content['source'][field], expected,
                    msg="field 'source.{}'".format(field))

class TestStatuses(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def _create_alice(self):
        self._alice = create_local_person(name='alice')

    def _create_status(self):
        self._status = create_local_status(
                content = 'Hello world.',
                posted_by = self._alice,
                )

    def test_get_status(self):

        self._create_alice()
        self._create_status()

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
                201,
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
                    201,
                    'Result code',
                    )

            content = json.loads(result.content.decode())

            self.assertLess(
                    previous_serial,
                    content['serial'])

            previous_serial = content['serial']


