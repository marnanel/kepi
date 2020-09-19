from unittest import skip
from rest_framework.test import force_authenticate, APIClient, APIRequestFactory
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings
import logging

# Tests for notifications. API docs are here:
# https://docs.joinmastodon.org/methods/notifications/
#
# In this module we test both the notification API methods
# and also the results of performing actions which cause
# notifications.

logger = logging.getLogger(name='kepi')

class TestNotifications(TrilbyTestCase):

    def test_follow(self):

        # recall that we're testing notifications here;
        # don't bother testing everything about follow

        alice = create_local_person(name='alice')
        bob   = create_local_person(name='bob')

        self.post(f'/api/v1/accounts/{alice.id}/follow',
                {
                    'reblogs': True, # FIXME we don't yet support this
                    },
                as_user = bob,
                )

        content = self.get('/api/v1/notifications',
                as_user = alice,
                )

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
                    'username': 'bob',
                    'acct': 'bob',
                    'url': 'https://testserver/users/bob',
                    },
                content[0]['account'],
                )

    def test_favourite(self):
        alice = create_local_person(name='alice')
        bob   = create_local_person(name='bob')

        status = create_local_status(
                content = 'Curiouser and curiouser!',
                posted_by = alice,
                )

        self.post(
                '/api/v1/statuses/{}/favourite'.format(status.id),
                {},
                as_user = bob,
                )

        content = self.get(
                '/api/v1/notifications',
                as_user = alice,
                )

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
                    'username': 'bob',
                    'acct': 'bob',
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
                    'content': '<p>Curiouser and curiouser!</p>',
                    },
                content[0]['status'],
                )

    @skip("Not yet implemented")
    def test_get_single(self):
        pass

    @skip("Not yet implemented")
    def test_clear(self):
        pass

    @skip("Not yet implemented")
    def test_clear_single(self):
        pass
