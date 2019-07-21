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

REMOTE_DAVE_ID = "https://dave.example.net/users/dave"
REMOTE_DAVE_DOMAIN = urlparse(REMOTE_DAVE_ID).netloc
REMOTE_DAVE_FOLLOWERS = REMOTE_DAVE_ID + 'followers'
REMOTE_DAVE_KEY = REMOTE_DAVE_ID + '#main-key'

ALICE_ID = 'https://altair.example.com/users/alice'
OUTBOX = ALICE_ID+'/outbox'
OUTBOX_PATH = '/users/alice/outbox'

BOB_ID = 'https://altair.example.com/users/bob'

# as given in https://www.w3.org/TR/activitypub/
OBJECT_FORM = {
        "@context": ["https://www.w3.org/ns/activitystreams",
            {"@language": "en"}],
        "type": "Note",
        'attributedTo': ALICE_ID,
        "name": "Chris liked 'Minimal ActivityPub update client'",
        "object": "https://rhiaro.co.uk/2016/05/minimal-activitypub",
        "to": ["https://rhiaro.co.uk/#amy",
            "https://dustycloud.org/followers",
            "https://rhiaro.co.uk/followers/"],
        "cc": "https://e14n.com/evan"
        }

CREATE_FORM = {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'id': ALICE_ID + '#foo',
        'actor': ALICE_ID,
        'type': 'Create',
        'object': OBJECT_FORM,
        }

logger = logging.getLogger(name='django_kepi')

class TestOutbox(TestCase):

    def _send(self,
            content,
            keys = None,
            sender = None,
            signed = True,
            ):

        settings.ALLOWED_HOSTS = [
                'altair.example.com',
                'testserver',
                ]

        if keys is None:
            keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        if sender is None:
            sender = create_local_person(
                    name = 'alice',
                    publicKey = keys['public'],
                    privateKey = keys['private'],
                    )

        f_body = dict([('f_'+f,v) for f,v in content.items()])

        body, headers = test_message_body_and_headers(
                secret = keys['private'],
                path = OUTBOX_PATH,
                key_id = sender['name']+'#main-key',
                signed = signed,
                **f_body,
                )

        headers=dict([('HTTP_'+f,v) for f,v in headers.items()])

        c = Client()
        response = c.post(OUTBOX,
                body,
                **headers,
                content_type='application/activity+json',
                )

        return response

    def test_no_signature(self):

        self._send(
                content = CREATE_FORM,
                signed = False,
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(ALICE_ID),
                )

        self.assertEqual(
                len(statuses),
                0)

    def test_create(self):

        self._send(
                content = CREATE_FORM,
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(ALICE_ID),
                )

        self.assertEqual(
                len(statuses),
                1)

    def test_post_by_remote_interloper(self):

        keys = json.load(open('tests/keys/keys-0002.json', 'r'))

        sender = create_remote_person(
                url = REMOTE_DAVE_ID,
                name = 'dave',
                publicKey = keys['public'],
                )

        create = CREATE_FORM
        create['actor'] = REMOTE_DAVE_ID
        create['id'] = REMOTE_DAVE_ID+'#foo'

        self._send(
                content = create,
                sender = sender,
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(REMOTE_DAVE_ID),
                )

        self.assertEqual(
                len(statuses),
                0)

    def test_post_by_local_interloper(self):

        keys1 = json.load(open('tests/keys/keys-0001.json', 'r'))
        keys2 = json.load(open('tests/keys/keys-0002.json', 'r'))

        create_local_person(
                name = 'alice',
                privateKey = keys1['private'],
                publicKey = keys1['public'],
                )

        sender = create_local_person(
                name = 'bob',
                privateKey = keys2['private'],
                publicKey = keys2['public'],
                )

        create = CREATE_FORM
        create['actor'] = sender.url
        create['id'] = sender.url+'#foo'

        self._send(
                content = create,
                sender = sender,
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(sender.id),
                )

        self.assertEqual(
                len(statuses),
                0)

    @httpretty.activate
    def test_unwrapped_object(self):

        items_before = list(Thing.objects.all())

        self._send(
                content = OBJECT_FORM,
                )

        items_after = list(Thing.objects.all())

        # This should have created two objects:
        # the Note we sent, and an implict Create.

        self.assertEqual(
                len(items_after)-len(items_before),
                2)

    def test_create_doesnt_work_on_activities(self):

        create = CREATE_FORM
        create['object']['type'] = 'Like'

        self._send(
                content = create,
                )

        activities = Activity.objects.all(
                )

        self.assertEqual(
                len(activities),
                0)


    def test_like(self):

        note = create_local_note(
                attributedTo = BOB_ID,
                )

        self._send(
                content = {
                    '@context': 'https://www.w3.org/ns/activitystreams',
                    'actor': ALICE_ID,
                    'type': 'Like',
                    'object': note.url,
                    }
            )

        self.assertEqual(
                len(Thing.objects.filter(f_actor=json.dumps(ALICE_ID))),
                1)

        # TODO When Actors have liked() and Things have likes(),
        # test those here too.

    def test_update(self):

        note = create_local_note(
                attributedTo = ALICE_ID,
                content = 'Twas brillig, and the slithy toves',
                )

        self.assertEqual(
                note['content'],
                'Twas brillig, and the slithy toves',
                )

        self._send(
                content = {
                    '@context': 'https://www.w3.org/ns/activitystreams',
                    'actor': ALICE_ID,
                    'type': 'Update',
                    'object': {
                        'id': note.url,
                        'content': 'did gyre and gimble in the wabe.',
                        },
                    }
            )

        note = Item.objects.get(f_attributedTo = json.dumps(ALICE_ID))

        self.assertEqual(
                note['content'],
                'did gyre and gimble in the wabe.',
                )

    def test_update_someone_elses(self):

        note = create_local_note(
                attributedTo = BOB_ID,
                content = 'Twas brillig, and the slithy toves',
                )

        self.assertEqual(
                note['content'],
                'Twas brillig, and the slithy toves',
                )

        self._send(
                content = {
                    '@context': 'https://www.w3.org/ns/activitystreams',
                    'actor': ALICE_ID,
                    'type': 'Update',
                    'object': {
                        'id': note.url,
                        'content': 'did gyre and gimble in the wabe.',
                        },
                    }
            )

        note = Item.objects.get(f_attributedTo = json.dumps(BOB_ID))

        # no change, because Alice doesn't own this note
        self.assertEqual(
                note['content'],
                'Twas brillig, and the slithy toves',
                )
