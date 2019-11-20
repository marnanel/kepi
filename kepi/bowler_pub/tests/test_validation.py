from django.test import TestCase, Client
from kepi.bowler_pub.validation import IncomingMessage, validate
from kepi.bowler_pub.models import AcObject
from unittest import skip
import httpretty
from . import *
import logging
import httpsig
import json

# FIXME This whole module should be rewritten to use httpretty

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

class TestValidationTasks(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    @httpretty.activate
    def test_local_lookup(self):

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))

        alice = create_local_person(
                name = 'alice',
                publicKey = keys['public'],
                )

        bob = create_local_person(
                name = 'bob',
                )

        body, headers = test_message_body_and_headers(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=LOCAL_ALICE,
                f_object=LOCAL_BOB,
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body,
                is_local_user=False)

        self.assertTrue(remote_object_is_recorded(ACTIVITY_ID),
                msg="Message passed validation")

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
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body,
                is_local_user=False)

        self.assertTrue(remote_object_is_recorded(ACTIVITY_ID),
                msg="Message passed validation")

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

        create_remote_person(
                url = REMOTE_FRED,
                name = 'Fred',
                publicKey=keys2['public'],
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys1['private'],
                )

        logger.info('Test message headers: %s',
                headers)
        logger.info('Test message body: %s',
                body)

        validate(path=INBOX_PATH,
                headers=headers,
                body=body,
                is_local_user=False)

        self.assertFalse(remote_object_is_recorded(ACTIVITY_ID),
                msg="Message failed validation")

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

        mock_remote_object(
                url = REMOTE_FRED,
                content = "They went away",
                status = 410,
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body,
                is_local_user=False)

        self.assertFalse(remote_object_is_recorded(ACTIVITY_ID),
                msg="Message failed validation")

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

        mock_remote_object(
                url = REMOTE_FRED,
                content = "They went away",
                status = 404,
                on_fetch = on_fetch,
                )

        body, headers = test_message_body_and_headers(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )

        validate(path=INBOX_PATH,
                headers=headers,
                body=body,
                is_local_user=False)

        self.assertFalse(remote_object_is_recorded(ACTIVITY_ID),
                msg="Message failed validation")

        self.assertTrue(
                fetched['fred'],
                msg="Fred's record was fetched from his server")

