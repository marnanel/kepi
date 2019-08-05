from django.test import TestCase
from unittest import skip
from tests import *
from django_kepi.create import create
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.mention import Mention
from django_kepi.models.item import Item
from django_kepi.models.thing import Thing
from django_kepi.models.following import Following
from django_kepi.models.activity import Activity
from django.test import Client
from urllib.parse import urlparse
import httpretty
import logging
import json

# This is a version of test_inbox based on test_outbox;
# they'll be merged in the future.

REMOTE_DAVE_ID = "https://dave.example.net/users/dave"
REMOTE_DAVE_DOMAIN = urlparse(REMOTE_DAVE_ID).netloc
REMOTE_DAVE_FOLLOWERS = REMOTE_DAVE_ID + 'followers'
REMOTE_DAVE_KEY = REMOTE_DAVE_ID + '#main-key'

ALICE_ID = 'https://altair.example.com/users/alice'
INBOX = ALICE_ID+'/inbox'
INBOX_HOST = 'altair.example.com'
ALICE_SOLE_INBOX_PATH = '/users/alice/inbox'

BOB_ID = 'https://bobs-computer.example.net/users/bob'
BOB_INBOX_URL = 'https://bobs-computer.example.net/users/bob/inbox'

# as given in https://www.w3.org/TR/activitypub/
OBJECT_FORM = {
        "@context": ["https://www.w3.org/ns/activitystreams",
            {"@language": "en"}],
        "type": "Note",
        'attributedTo': BOB_ID,
        "name": "Chris liked 'Minimal ActivityPub update client'",
        "object": "https://rhiaro.co.uk/2016/05/minimal-activitypub",
        "to": [ALICE_ID,
            "https://dustycloud.org/followers",
            "https://rhiaro.co.uk/followers/"],
        "cc": "https://e14n.com/evan"
        }

MIME_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
INVALID_UTF8 = b"\xa0\xa1"

logger = logging.getLogger(name='django_kepi')

class TestInbox2(TestCase):

    def _send(self,
            content,
            recipient = None,
            recipientKeys = None,
            sender = None,
            senderKeys = None,
            path = INBOX_PATH,
            ):

        settings.ALLOWED_HOSTS = [
                'altair.example.com',
                'testserver',
                ]

        if recipientKeys is None:
            recipientKeys = json.load(open('tests/keys/keys-0001.json', 'r'))

        if recipient is None:
            recipient = create_local_person(
                    name = 'alice',
                    publicKey = recipientKeys['public'],
                    privateKey = recipientKeys['private'],
                    )

        if senderKeys is None:
            senderKeys = json.load(open('tests/keys/keys-0002.json', 'r'))

        if sender is None:
            sender = create_remote_person(
                    url = BOB_ID,
                    name = 'bob',
                    inbox = BOB_INBOX_URL,
                    publicKey = senderKeys['public'],
                    )

        if not isinstance(content, dict):
            # Overriding the usual content.
            # This is used for things like checking
            # whether non-JSON content is handled correctly.

            f_body = {'content': content}
            content = {}

        if '@context' not in content:
            content['@context'] = 'https://www.w3.org/ns/activitystreams'

        if 'id' not in content:
            content['id'] = BOB_ID+'#foo'

        if 'actor' not in content:
            content['actor'] = BOB_ID

        f_body = dict([('f_'+f,v) for f,v in content.items()])
        response = post_test_message(
                path = path,
                host = INBOX_HOST,
                secret = senderKeys['private'],
                **f_body,
                )

        return response

    @httpretty.activate
    def test_create(self):

        self._send(
                content = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    'to': OBJECT_FORM['to'],
                    'cc': OBJECT_FORM['cc'],
                    },
                )

        items = Item.objects.filter(
                f_attributedTo=BOB_ID,
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
                content = {
                    'type': 'Follow',
                    'object': ALICE_ID,
                    'actor': BOB_ID,
                    },
                )

        self.assertDictContainsSubset(
                subset = {
                    "actor": "https://altair.example.com/users/alice",
                    "to": [
                        "https://bobs-computer.example.net/users/bob"
                        ],
                    "type": "Accept"
                    },
                dictionary = json.loads(httpretty.last_request().body),
        msg='Acceptance of follow request matched')

    @httpretty.activate
    def test_sole_inbox(self):
        recipientKeys = json.load(open('tests/keys/keys-0001.json', 'r'))
        recipient = create_local_person(
                name = 'alice',
                publicKey = recipientKeys['public'],
                privateKey = recipientKeys['private'],
                inbox = ALICE_SOLE_INBOX_PATH,
                )

        self._send(
                content = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    'to': OBJECT_FORM['to'],
                    'cc': OBJECT_FORM['cc'],
                    },
                recipient = recipient,
                path = ALICE_SOLE_INBOX_PATH,
                )

        items = Item.objects.filter(
                f_attributedTo=BOB_ID,
                )

        self.assertEqual(
                len(items),
                1)

    @httpretty.activate
    def test_shared_inbox(self):
        recipientKeys = json.load(open('tests/keys/keys-0001.json', 'r'))
        recipient = create_local_person(
                name = 'alice',
                publicKey = recipientKeys['public'],
                privateKey = recipientKeys['private'],
                inbox = ALICE_SOLE_INBOX_PATH,
                sharedInbox = INBOX_PATH,
                )

        self._send(
                content = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    'to': OBJECT_FORM['to'],
                    'cc': OBJECT_FORM['cc'],
                    },
                recipient = recipient,
                path = INBOX_PATH,
                )

        items = Item.objects.filter(
                f_attributedTo=BOB_ID,
                )

        self.assertEqual(
                len(items),
                1)

    @httpretty.activate
    def test_non_json(self):

        self._send(
                content = 'Hello',
                )

        items = Item.objects.filter(
                f_attributedTo=BOB_ID,
                )

        self.assertEqual(
                len(items),
                0)

    @httpretty.activate
    def test_invalid_utf8(self):

        self._send(
                content = INVALID_UTF8,
                )

        items = Item.objects.filter(
                f_attributedTo=BOB_ID,
                )

        self.assertEqual(
                len(items),
                0)
