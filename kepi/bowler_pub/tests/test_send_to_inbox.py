from django.test import TestCase
from unittest import skip
from kepi.bowler_pub.tests import *
from django.test import Client
from urllib.parse import urlparse
from kepi.trilby_api.tests import create_local_person
from kepi.trilby_api.models import Status
import httpretty
import json
import logging

logger = logging.getLogger(name='kepi')

REMOTE_DAVE_ID = "https://dave.example.net/users/dave"
REMOTE_DAVE_DOMAIN = urlparse(REMOTE_DAVE_ID).netloc
REMOTE_DAVE_FOLLOWERS = REMOTE_DAVE_ID + 'followers'
REMOTE_DAVE_KEY = REMOTE_DAVE_ID + '#main-key'

ALICE_ID = 'https://testserver/users/alice'
INBOX = ALICE_ID+'/inbox'
INBOX_HOST = 'testserver'
ALICE_SOLE_INBOX_PATH = '/users/alice/inbox'

BOB_ID = 'https://bobs-computer.example.net/users/bob'
BOB_INBOX_URL = 'https://bobs-computer.example.net/users/bob/inbox'

OBJECT_FORM = {
        "@context": ["https://www.w3.org/ns/activitystreams",
            {"@language": "en"}],
        "id": "https://bobs-computer.example.net/object/1",
        "type": "Note",
        'attributedTo': BOB_ID,
        "content": "Chris liked 'Minimal ActivityPub update client'",
        "object": "https://rhiaro.co.uk/2016/05/minimal-activitypub",
        "to": [ALICE_ID,
            "https://dustycloud.org/followers",
            "https://rhiaro.co.uk/followers/"],
        "cc": "https://e14n.com/evan"
        }

MIME_TYPE = 'application/activity+json'
INVALID_UTF8 = b"\xa0\xa1"

logger = logging.getLogger(name='kepi')

class Tests(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'
        settings.ALLOWED_HOSTS = ['testserver']

    def _send(self,
            message,
            recipient = None,
            recipientKeys = None,
            sender = None,
            senderKeys = None,
            path = INBOX_PATH,
            ):

        if recipient is None:
            recipient = create_local_person(
                    name = 'alice',
                    )

        if senderKeys is None:
            senderKeys = json.load(open('kepi/bowler_pub/tests/keys/keys-0002.json', 'r'))

        if sender is None:
            sender = create_remote_person(
                    url = BOB_ID,
                    name = 'bob',
                    publicKey = senderKeys['public'],
                    auto_fetch = True,
                    )

        self._sender = sender

        if not isinstance(message, dict):
            # This is used for things like checking
            # whether non-JSON content is handled correctly.

            content = message
            fields = {}

        else:

            # "message" is a dict

            content = None
            fields = message.copy()

            if 'id' not in fields:
                fields['id'] = BOB_ID+'#foo'

            if 'actor' not in fields:
                fields['actor'] = BOB_ID

        response = post_test_message(
                path = path,
                host = INBOX_HOST,
                secret = senderKeys['private'],
                content = content,
                fields = fields,
                )

        logger.debug("Response code: %s", response.status_code)
        if response.status_code!=200:
            logger.debug("Response body: %s", response.content)

        return response

    @httpretty.activate
    def test_create(self):

        self._send(
                message = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    'to': OBJECT_FORM['to'],
                    'cc': OBJECT_FORM['cc'],
                    },
                )

        items = Status.objects.filter(
                account = self._sender,
                )

        self.assertEqual(
                len(items),
                1)

    @httpretty.activate
    def test_follow(self):

        httpretty.register_uri(
                httpretty.POST,
                BOB_INBOX_URL,
                status=200,
                body='Thank you!',
                )

        self._send(
                message = {
                    'type': 'Follow',
                    'object': ALICE_ID,
                    'actor': BOB_ID,
                    },
                )

        self.assertDictContainsSubset(
                subset = {
                    "actor": "https://testserver/users/alice",
                    "to": [
                        "https://bobs-computer.example.net/users/bob"
                        ],
                    "type": "Accept"
                    },
                dictionary = json.loads(httpretty.last_request().body),
        msg='Acceptance of follow request matched')

    @httpretty.activate
    def test_sole_inbox(self):
        recipient = create_local_person(
                name = 'alice',
                )

        self._send(
                message = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    'to': OBJECT_FORM['to'],
                    'cc': OBJECT_FORM['cc'],
                    },
                recipient = recipient,
                path = ALICE_SOLE_INBOX_PATH,
                )

        items = Status.objects.filter(
                account = self._sender,
                )

        self.assertEqual(
                len(items),
                1)

    @httpretty.activate
    def test_shared_inbox(self):
        recipient = create_local_person(
                name = 'alice',
                )

        self._send(
                message = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    'to': OBJECT_FORM['to'],
                    'cc': OBJECT_FORM['cc'],
                    },
                recipient = recipient,
                path = INBOX_PATH,
                )

        items = Status.objects.filter(
                account = self._sender,
                )

        self.assertEqual(
                len(items),
                1)

    @httpretty.activate
    def test_non_json(self):

        self._send(
                message = 'Hello',
                )

        items = Status.objects.filter(
                account = self._sender,
                )

        self.assertEqual(
                len(items),
                0)

    @httpretty.activate
    def test_invalid_utf8(self):

        self._send(
                message = INVALID_UTF8,
                )

        items = Status.objects.filter(
                account = self._sender,
                )

        self.assertEqual(
                len(items),
                0)
