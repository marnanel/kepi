from django.test import TestCase, Client
from kepi.bowler_pub.validation import validate
import kepi.trilby_api.models as trilby_models
from unittest import skip
import httpretty
from . import *
from kepi.trilby_api.tests import create_local_person, create_local_status
import logging
import httpsig
import json

# FIXME much refactoring could be done here

# FIXME test caching
# FIXME test invalid keys

logger = logging.getLogger(name='kepi')

ACTIVITY_ID = "https://example.com/04b065f8-81c4-408e-bec3-9fb1f7c06408"
INBOX_HOST = 'europa.example.com'
INBOX_PATH = '/sharedInbox'

REMOTE_FRED = 'https://remote.example.org/users/fred'
REMOTE_JIM = 'https://remote.example.org/users/jim'

FREDS_INBOX = REMOTE_FRED+'/inbox'
JIMS_INBOX = REMOTE_JIM+'/inbox'
REMOTE_SHARED_INBOX = 'https://remote.example.org/shared-inbox'

LOCAL_ALICE = 'https://testserver/users/alice'
LOCAL_BOB = 'https://testserver/users/bob'

class TestValidation(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    @httpretty.activate
    def test_local_lookup(self):

        from kepi.trilby_api.models import Follow

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))

        alice = create_local_person(
                name = 'alice',
                publicKey = keys['public'],
                )

        bob = create_local_person(
                name = 'bob',
                )

        body, headers = test_message_body_and_headers(
                fields = {
                    'id': ACTIVITY_ID,
                    'type': "Follow",
                    'actor': LOCAL_ALICE,
                    'object': LOCAL_BOB,
                    },
                secret = keys['private'],
                )

        create_remote_person(
                LOCAL_ALICE,
                'Alice',
                load_default_keys_from='kepi/bowler_pub/tests/keys/keys-0001.json',
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body)

        self.assertTrue(
                Follow.objects.filter(
                    follower = alice,
                    following = bob,
                    ).exists(),
                msg="Message passed validation",
                )

    @httpretty.activate
    def test_remote_user_known(self):

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))
        fetched = {
                'fred': False,
                }
        def on_fetch():
            fetched['fred'] = True

        alice = create_local_person(
                name = 'alice',
                )

        create_remote_person(
                url = REMOTE_FRED,
                name = 'Fred',
                publicKey=keys['public'],
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                fields = {
                    'id': ACTIVITY_ID,
                    'type': "Follow",
                    'actor': REMOTE_FRED,
                    'object': LOCAL_ALICE,
                    },
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body)

        self.assertEqual(
                len(trilby_models.Follow.objects.filter(
                    following=alice,
                    )),
                1,
                msg="The message validated successfully")

        fred = trilby_models.RemotePerson.objects.get(
            url=REMOTE_FRED,
            )

        self.assertEqual(fred.status,
                200,
                msg="Fred's record was stored locally as OK")

        self.assertTrue(
                fetched['fred'],
                msg="Fred's record was fetched from his server")

    @httpretty.activate
    def test_remote_user_spoofed(self):

        keys1 = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))
        keys2 = json.load(open('kepi/bowler_pub/tests/keys/keys-0002.json', 'r'))

        fetched = {
                'fred': False,
                }

        def on_fetch():
            fetched['fred'] = True

        alice = create_local_person(
                name = 'alice',
                )

        create_remote_person(
                url = REMOTE_FRED,
                name = 'Fred',
                publicKey=keys2['public'],
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                fields = {
                    'id': ACTIVITY_ID,
                    'type': "Follow",
                    'actor': REMOTE_FRED,
                    'object': LOCAL_ALICE,
                    },
                secret = keys1['private'],
                )

        logger.info('Test message headers: %s',
                headers)
        logger.info('Test message body: %s',
                body)

        validate(path=INBOX_PATH,
                headers=headers,
                body=body)

        self.assertEqual(
                len(trilby_models.Follow.objects.filter(
                    following=alice,
                    )),
                0,
                msg="The message did not validate")

        self.assertTrue(
                fetched['fred'],
                msg="Fred's record was fetched from his server")

    @httpretty.activate
    def test_remote_user_gone(self):

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))
        fetched = {
                'fred': False,
                }
        def on_fetch():
            fetched['fred'] = True

        alice = create_local_person(
                name = 'alice',
                )

        mock_remote_object(
                url = REMOTE_FRED,
                content = "They went away",
                status = 410,
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                fields = {
                    'id': ACTIVITY_ID,
                    'type': "Follow",
                    'actor': REMOTE_FRED,
                    'object': LOCAL_ALICE,
                    },
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body)

        self.assertEqual(
                len(trilby_models.Follow.objects.filter(
                    following=alice,
                    )),
                0,
                msg="The message did not validate")

        fred = trilby_models.RemotePerson.objects.get(
            url=REMOTE_FRED,
            )

        self.assertEqual(fred.status,
                410,
                msg="Fred's record was stored locally as Gone")

        self.assertTrue(
                fetched['fred'],
                msg="Fred's record was fetched from his server")

    @httpretty.activate
    def test_remote_user_unknown(self):

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))
        fetched = {
                'fred': False,
                }
        def on_fetch():
            fetched['fred'] = True

        alice = create_local_person(
                name = 'alice',
                )

        mock_remote_object(
                url = REMOTE_FRED,
                content = "Who? Never heard of them",
                status = 404,
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                fields = {
                    'id': ACTIVITY_ID,
                    'type': "Follow",
                    'actor': REMOTE_FRED,
                    'object': LOCAL_ALICE,
                    },
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body)

        self.assertEqual(
                len(trilby_models.Follow.objects.filter(
                    following=alice,
                    )),
                0,
                msg="The message did not validate")

        self.assertTrue(
                fetched['fred'],
                msg="Fred's record was fetched from his server")
