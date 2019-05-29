from django.test import TestCase, Client
from django_kepi.delivery import deliver
from django_kepi.models import Thing
from unittest.mock import Mock, patch
from . import *
import logging
import httpsig
import json

# FIXME test caching
# FIXME test invalid keys

logger = logging.getLogger(name='django_kepi')

def _message_became_activity(url=ACTIVITY_ID):
    try:
        result = Thing.objects.get(remote_url=url)
        return True
    except Thing.DoesNotExist:
        return False

class ResultWrapper(object):
    def __init__(self,
            text='',
            status_code=200,
            ):
        self.text = json.dumps(text)
        self.status_code = status_code

class TestDeliverTasks(TestCase):

    def _run_delivery(
            self,
            activity_fields,
            remote_user_details,
            ):

        a = Thing.create(activity_fields)
        a.save()

        def _get(url):
            if url in remote_user_details:
                return ResultWrapper(
                        text=remote_user_details[url],
                        )
            else:
                return ResultWrapper(
                    status_code = 404,
                    )

        mock_get = Mock(
                side_effect = _get,
                )

        mock_post = Mock(
                return_value = None,
                )

        with patch('requests.get', mock_get):
            with patch('requests.post', mock_post):
                deliver(a.number)

    def test_deliver_remote(self):

        keys = json.load(open('tests/keys/keys-0000.json', 'r'))
        alice = create_local_person(
                name = 'alice',
                publicKey = keys['public'],
                # XXX FIXME this is a really silly place to store the private key
                privateKey = keys['private'],
                )
        alice.save()

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
                    }
                )

    def test_deliver_local(self):

        keys0 = json.load(open('tests/keys/keys-0000.json', 'r'))
        keys1 = json.load(open('tests/keys/keys-0001.json', 'r'))
        alice = create_local_person(
                name = 'alice',
                publicKey = keys0['public'],
                privateKey = keys0['private'],
                )
        alice.save()
        bob = create_local_person(
                name = 'bob',
                publicKey = keys1['public'],
                privateKey = keys1['private'],
                )
        bob.save()

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': LOCAL_BOB,
                    'to': [LOCAL_BOB],
                    },
                remote_user_details = {
                    }
                )

# for investigation, rather than long-term testing
class TestBob(TestCase):
    def test_bob(self):
        alice = create_local_person(
                name = 'alice',
                )
        alice.save()

        bob = create_local_person(
                name = 'bob',
                )
        bob.save()

        # XXX add follower / following.
        # XXX create_local_person's view is not embellishing its activity_form.

        c = Client()
        logger.info('bob %s', c.get('/users/bob').content)
        logger.info('bob friends %s', c.get('/users/bob/following').content)
        logger.info('bob friends p1 %s', c.get('/users/bob/following?page=1').content)

# This is purely about delivery, so we only use one Thing type: a Like.
# {
#    "type": "Like",
#    "actor": "alice@altair.example.com",
#    "object": "https://example.com",
#  (here: to, cc, bto, bcc, as appropriate)
# }

# These tests are all written with respect to a small group of users:
#
# Local users:
#   alice@altair.example.com
#       follows: bob, quebec, yankee
#   bob@altair.example.com
#       follows: quebec, yankee, zulu
#
# Remote users:
#   quebec@montreal.example.net
#       personal inbox: https://montreal.example.net/users/quebec
#       no shared inbox.
#       follows: alice, zulu
#
#   yankee@example.net
#       personal inbox: https://example.net/yankee
#       shared inbox: https://example.net/sharedInbox
#       follows: alice, bob
#
#   zulu@example.net
#       personal inbox: https://example.net/zulu
#       shared inbox: https://example.net/sharedInbox
#       follows: alice, bob, quebec, yankee
#
# As ever, public messages:
#   https://www.w3.org/ns/activitystreams#Public
#    (or, "as:Public", or "Public"; all three are synonyms)
#
# Generally, each test asserts that a particular set of
# inboxes were delivered to.
#
# XXX Extra: make proof against infinite recursion honeytrap.
