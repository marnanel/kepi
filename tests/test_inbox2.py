from django.test import TestCase
from unittest import skip
from tests import *
from django_kepi.create import create
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.mention import Mention
from django_kepi.models.item import Item
from django_kepi.models.thing import Thing
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
INBOX_PATH = '/users/alice/inbox'

BOB_ID = 'https://bobs-computer.example.net/users/bob'

# as given in https://www.w3.org/TR/activitypub/
OBJECT_FORM = {
        "@context": ["https://www.w3.org/ns/activitystreams",
            {"@language": "en"}],
        "type": "Note",
        'attributedTo': BOB_ID,
        "name": "Chris liked 'Minimal ActivityPub update client'",
        "object": "https://rhiaro.co.uk/2016/05/minimal-activitypub",
        "to": ["https://rhiaro.co.uk/#amy",
            "https://dustycloud.org/followers",
            "https://rhiaro.co.uk/followers/"],
        "cc": "https://e14n.com/evan"
        }

logger = logging.getLogger(name='django_kepi')

class TestInbox2(TestCase):

    @httpretty.activate
    def _send(self,
            content,
            keys = None,
            recipient = None,
            recipientKeys = None,
            sender = None,
            senderKeys = None,
            signed = True,
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
                    publicKey = senderKeys['public'],
                    )

        if '@context' not in content:
            content['@context'] = 'https://www.w3.org/ns/activitystreams'

        if 'id' not in content:
            content['id'] = BOB_ID+'#foo'

        if 'actor' not in content:
            content['actor'] = BOB_ID

        f_body = dict([('f_'+f,v) for f,v in content.items()])

        body, headers = test_message_body_and_headers(
                secret = senderKeys['private'],
                path = INBOX_PATH,
                key_id = BOB_ID+'#main-key',
                signed = signed,
                **f_body,
                )

        headers=dict([('HTTP_'+f,v) for f,v in headers.items()])

        c = Client()
        response = c.post(INBOX,
                body,
                **headers,
                content_type='application/activity+json',
                )

        return response

    def test_create(self):

        self._send(
                content = {
                    'type': 'Create',
                    'object': OBJECT_FORM,
                    },
                )

        items = Item.objects.filter(
                f_attributedTo=json.dumps(BOB_ID),
                )

        self.assertEqual(
                len(items),
                1)

        # FIXME also check whether it appears in Alice's inbox
        # as seen by Alice
