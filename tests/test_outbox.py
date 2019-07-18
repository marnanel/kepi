from django.test import TestCase
from unittest import skip
from tests import create_local_note, create_local_person, \
    create_remote_person, test_message_body_and_headers
from django_kepi.create import create
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.mention import Mention
from django_kepi.models.item import Item
from django_kepi.models.thing import Thing
from django.test import Client
from urllib.parse import urlparse
import httpretty
import logging
import json

SENDER_ID = "https://dustycloud.org/chris/"
SENDER_DOMAIN = urlparse(SENDER_ID).netloc
SENDER_FOLLOWERS = SENDER_ID + 'followers'
SENDER_KEY = SENDER_ID + '#main-key'

RECIPIENT_ID = 'https://altair.example.com/users/alice'
OUTBOX = RECIPIENT_ID+'/outbox'
OUTBOX_PATH = '/users/alice/outbox'

# as given in https://www.w3.org/TR/activitypub/
OBJECT_FORM = {
        "@context": ["https://www.w3.org/ns/activitystreams",
            {"@language": "en"}],
        "type": "Note",
        'attributedTo': SENDER_ID,
        "name": "Chris liked 'Minimal ActivityPub update client'",
        "object": "https://rhiaro.co.uk/2016/05/minimal-activitypub",
        "to": ["https://rhiaro.co.uk/#amy",
            "https://dustycloud.org/followers",
            "https://rhiaro.co.uk/followers/"],
        "cc": "https://e14n.com/evan"
        }

CREATE_FORM = {
        '@context': 'https://www.w3.org/ns/activitystreams',
        'id': SENDER_ID + '#foo',
        'actor': SENDER_ID,
        'type': 'Create',
        'object': OBJECT_FORM,
        }

logger = logging.getLogger(name='django_kepi')

class TestOutbox(TestCase):

    def test_no_signature(self):

        c = Client()
        response = c.post(OUTBOX,
                OBJECT_FORM,
                content_type='application/activity+json',
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(SENDER_ID),
                )

        self.assertEqual(
                len(statuses),
                0)

    @httpretty.activate
    def test_create(self):

        body = dict([('f_'+f,v) for f,v in CREATE_FORM.items()])

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        body, headers = test_message_body_and_headers(
                secret = keys['private'],
                path = OUTBOX_PATH,
                key_id = SENDER_KEY,
                **body,
                )

        headers=dict([('HTTP_'+f,v) for f,v in headers.items()])

        create_remote_person(
                url = SENDER_ID,
                name = 'Example person',
                publicKey = keys['public'],
                )

        c = Client()
        response = c.post(OUTBOX,
                bytes(json.dumps(CREATE_FORM),
                    encoding='UTF-8'),
                **headers,
                content_type='application/activity+json',
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(SENDER_ID),
                )

        logger.debug('List of items by %s: %s',
                SENDER_ID, list(statuses))

        self.assertEqual(
                len(statuses),
                1)

    def test_unwrapped_object(self):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        body, headers = test_message_body_and_headers(
                secret = keys['private'],
                path = OUTBOX_PATH,
                )
        print(body, headers)

        c = Client()
        response = c.post(OUTBOX,
                json.dumps(OBJECT_FORM),
                content_type='application/activity+json',
                )

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(SENDER_ID),
                )

        self.assertEqual(
                len(statuses),
                0)

    @skip("not implemented")
    def test_create_doesnt_work_on_activites(self):
        pass


