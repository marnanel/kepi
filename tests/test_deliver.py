from django.test import TestCase, Client
from django_kepi.delivery import deliver
from django_kepi.models import Thing
import django_kepi.views
from unittest.mock import Mock, patch
from . import *
import logging
import httpsig
import httpretty
import json
import requests

# FIXME test caching
# FIXME test invalid keys

logger = logging.getLogger(name='django_kepi')

REMOTE_PATH_NAMES = {
        '/users/fred/inbox': 'fred',
        '/users/jim/inbox': 'jim',
        }

def _message_became_activity(url=ACTIVITY_ID):
    try:
        result = Thing.objects.get(remote_url=url)
        return True
    except Thing.DoesNotExist:
        return False

class TestDeliverTasks(TestCase):

    def _run_delivery(
            self,
            activity_fields,
            remote_user_details,
            remote_user_endpoints,
            ):

        a = Thing.create(**activity_fields)
        a.save()

        for who, what in remote_user_details.items():
            mock_remote_object(
                    url = who,
                    content = json.dumps(what),
                    )

        for who in remote_user_endpoints:
            mock_remote_object(
                    url = who,
                    content = 'Thank you',
                    as_post = True,
                    )

        deliver(a.number)

    @httpretty.activate
    def test_deliver_remote(self):

        keys = json.load(open('tests/keys/keys-0000.json', 'r'))

        alice = create_local_person(
                name = 'alice',
                publicKey = keys['public'],
                privateKey = keys['private'],
                )

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': REMOTE_FRED,
                    'to': [REMOTE_FRED],
                    },
                remote_user_details = {
                    REMOTE_FRED: remote_user(
                        url=REMOTE_FRED,
                        name='Fred',
                        sharedInbox=REMOTE_SHARED_INBOX,
                        ),
                    },
                remote_user_endpoints = [
                    REMOTE_SHARED_INBOX,
                    ],
                )

    @httpretty.activate
    def test_deliver_local(self):

        keys0 = json.load(open('tests/keys/keys-0000.json', 'r'))
        keys1 = json.load(open('tests/keys/keys-0001.json', 'r'))
        alice = create_local_person(
                name = 'alice',
                publicKey = keys0['public'],
                privateKey = keys0['private'],
                )
        bob = create_local_person(
                name = 'bob',
                publicKey = keys1['public'],
                privateKey = keys1['private'],
                )

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': LOCAL_BOB,
                    'to': [LOCAL_BOB],
                    },
                remote_user_details = {
                    },
                remote_user_endpoints = [
                    ],
                )

        # FIXME add some assertions!

# for investigation, rather than long-term testing
class TestBob(TestCase):
    def test_bob(self):
        alice = create_local_person(
                name = 'alice',
                )

        bob = create_local_person(
                name = 'bob',
                )

        # XXX add follower / following.
        # XXX create_local_person's view is not embellishing its activity_form.

        c = Client()
        logger.info('bob %s', c.get('/users/bob').content)
        logger.info('bob friends %s', c.get('/users/bob/following').content)
        logger.info('bob friends p1 %s', c.get('/users/bob/following?page=1').content)

# XXX Extra: make proof against infinite recursion honeytrap.
# XXX Extra: check bcc and bto don't appear in the sent messages.
# XXX Extra: check all versions of "Public" are equivalent.
# XXX Extra: check what happens if the remote key is junk

class TestDelivery(TestCase):

    def _set_up_remote_user_mocks(self):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        # XXX These also need follower collections

        create_remote_person(
                url = REMOTE_FRED,
                name = 'fred',
                publicKey = keys['public'],
                inbox = FREDS_INBOX,
                followers = FREDS_FOLLOWERS,
                )

        create_remote_collection(
                url = FREDS_FOLLOWERS,
                items=[
                    REMOTE_JIM,
                    LOCAL_ALICE,
                    LOCAL_BOB,
                    ],
                )

        create_remote_person(
                url = REMOTE_JIM,
                name = 'jim',
                publicKey = keys['public'],
                inbox = JIMS_INBOX,
                followers = JIMS_FOLLOWERS,
                )

        create_remote_collection(
                url = JIMS_FOLLOWERS,
                items=[
                    LOCAL_BOB,
                    ],
                )

    def _set_up_remote_request_mocks(self):
        mock_remote_object(
                FREDS_INBOX,
                as_post = True,
                )

        mock_remote_object(
                JIMS_INBOX,
                as_post = True,
                )

    def _set_up_local_user_mocks(self):

        keys = json.load(open('tests/keys/keys-0002.json', 'r'))

        # I know these aren't mocks. This is just for consistency.
        create_local_person(name='alice',
                privateKey = keys['private'])
        create_local_person(name='bob')

    @patch.object(django_kepi.views.InboxView, 'post')
    @httpretty.activate
    def _test_delivery(self,
            fake_local_request,
            to,
            expected,
            ):

        self._set_up_remote_user_mocks()
        self._set_up_remote_request_mocks()
        self._set_up_local_user_mocks()

        like = Thing.create(
                f_type = 'Like',
                f_actor = LOCAL_ALICE,
                f_object = REMOTE_FRED,
                to = to,
                )
        like.save()

        deliver(like.number)

        #################
        # Assertions

        touched = []
        for req in httpretty.httpretty.latest_requests:
            if req.method=='POST':
                touched.append(
                        REMOTE_PATH_NAMES.get(req.path, req.path),
                        )

        for req in fake_local_request.mock_calls:
            kwargs = req[2]
            if 'name' not in kwargs:
                continue

            if kwargs['name'] is None:
                touched.append('shared-local')
            else:
                touched.append(kwargs['name'])

        logger.info('Inboxes touched: %s', touched)
        logger.info('  " "  expected: %s', expected)

        self.assertListEqual(
                sorted(touched),
                sorted(expected),
                )

    def test_simple_remote_and_local(self):
        self._test_delivery(
                to=[REMOTE_FRED, LOCAL_BOB],
                expected=['fred', 'shared-local'],
                )

    def test_simple_local(self):
        self._test_delivery(
                to=[LOCAL_BOB],
                expected=['shared-local'],
                )

    def test_simple_remote(self):
        self._test_delivery(
                to=[REMOTE_FRED],
                expected=['fred'],
                )

    def test_not_to_self(self):
        self._test_delivery(
                to=[LOCAL_ALICE],
                expected=[],
                )

    def test_not_to_public_url(self):
        self._test_delivery(
                to=[PUBLIC],
                expected=[],
                )

    def test_not_to_public_as(self):
        self._test_delivery(
                to=['as:Public'],
                expected=[],
                )

    def test_not_to_public_bare(self):
        self._test_delivery(
                to=['Public'],
                expected=[],
                )

    def test_remote_followers(self):
        self._test_delivery(
                to=[REMOTE_FRED, FREDS_FOLLOWERS],
                expected=['fred', 'jim', 'bob'],
                )
