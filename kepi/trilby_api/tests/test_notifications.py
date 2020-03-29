from django.test import TestCase
from rest_framework.test import force_authenticate, APIClient, APIRequestFactory
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from django.conf import settings
import logging
import httpretty

logger = logging.getLogger(name='kepi')

DEFAULT_KEYS_FILENAME = 'kepi/bowler_pub/tests/keys/keys-0002.json'
TESTSERVER = 'testserver'

class TestNotifications(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = TESTSERVER

    @httpretty.activate
    def test_follow(self):
        alice = create_local_person(name='alice')

        fred_keys = json.load(open(DEFAULT_KEYS_FILENAME, 'r'))

        fred = create_remote_person(
                name='fred',
                publicKey = fred_keys['public'],
                url=REMOTE_FRED,
                )

        post_test_message(
                secret = fred_keys['private'],
                host = TESTSERVER,
                f_type = 'Follow',
                f_actor = REMOTE_FRED,
                f_object = alice.actor.url,
                )

        request = self.factory.get(
                '/api/v1/notifications/',
                )
        force_authenticate(request, user=alice.local_user)

        view = Notifications.as_view()
        result = view(request)
        result.render()

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content.decode())

        self.assertEqual(
                len(content),
                1,
                )

        self.assertDictContainsSubset(
                {
                    'type': 'follow',
                    },
                content[0],
                )

        self.assertIn(
                'account',
                content[0],
                )

        self.assertDictContainsSubset(
                {
                    'id': 'https://remote.example.org/users/fred',
                    'username': 'fred',
                    'acct': 'fred@remote.example.org',
                    'url': 'https://remote.example.org/users/fred',
                    },
                content[0]['account'],
                )

    @httpretty.activate
    def test_favourite(self):
        alice = create_local_person(name='alice')
        bob   = create_local_person(name='bob')

        status = create_local_status(
                content = 'Curiouser and curiouser!',
                posted_by = alice,
                )

        c_bob = APIClient()
        c_bob.force_authenticate(bob.local_user)

        result = c_bob.post(
                '/api/v1/statuses/{}/favourite'.format(status.id),
                {},
                format = 'json',
                )

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        c_alice = APIClient()
        c_alice.force_authenticate(alice.local_user)

        result = c_alice.get(
                '/api/v1/notifications',
                )

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content.decode())

        self.assertEqual(
                len(content),
                1,
                )

        self.assertDictContainsSubset(
                {
                    'type': 'favourite',
                    },
                content[0],
                )

        self.assertIn(
                'account',
                content[0],
                )

        self.assertDictContainsSubset(
                {
                    'id': 'https://testserver/users/bob',
                    'username': 'bob',
                    'acct': 'bob@testserver',
                    'url': 'https://testserver/users/bob',
                    },
                content[0]['account'],
                )

        self.assertIn(
                'status',
                content[0],
                )

        self.assertDictContainsSubset(
                {
                    'id': str(status.id),
                    'content': 'Curiouser and curiouser!',
                    },
                content[0]['status'],
                )
