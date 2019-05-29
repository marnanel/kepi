from django.test import TestCase, Client
from django_kepi.views import InboxView
from django_kepi.models import Thing, create, Following
from django_kepi.validation import IncomingMessage
from unittest import skip
from . import *
import json
import httpretty
import logging

logger = logging.getLogger(name='django_kepi')

class TestInbox(TestCase):

    @httpretty.activate
    def test_specific_post(self):

        ALICE_INBOX = '/users/alice/inbox'

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        alice = create_local_person(
                name='alice',
                auto_follow=False,
                )

        create_remote_person(
                name='fred',
                url=REMOTE_FRED,
                publicKey = keys['public'],
                )

        post_test_message(
            path = ALICE_INBOX,
            secret = keys['private'],
            f_type = "Follow",
            f_actor = REMOTE_FRED,
            f_object = LOCAL_ALICE,
            )

        self.assertIs(
                len(Following.objects.filter(
                    follower = REMOTE_FRED,
                    following = LOCAL_ALICE,
                    )),
                1,
                msg="sending Follow did not result in following")

    @httpretty.activate
    def test_shared_post(self):

        HUMAN_URL = 'https://users.example.net/mary'
        ANIMAL_URL = 'https://things.example.org/another-lamb'

        mock_remote_object(HUMAN_URL, ftype='Person')
        mock_remote_object(ANIMAL_URL, ftype='Person')

        c = Client()

        c.post('/sharedInbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "actor": HUMAN_URL,
                    "object": ANIMAL_URL,
                    "type": "Like",
                    },
                )

    @skip("broken; find out why")
    def test_non_json(self):

        IncomingMessage.objects.all().delete()

        c = Client()

        c.post('/sharedInbox',
                content_type = 'text/plain',
                data = 'Hello',
                )

        self.assertFalse(
                IncomingMessage.objects.all().exists())

    @httpretty.activate
    def test_malformed_json(self):

        HUMAN_URL = 'https://users.example.com/my-dame'
        ANIMAL_URL = 'https://animals.example.com/a-lame-tame-crane'

        mock_remote_object(HUMAN_URL, ftype='Person')
        mock_remote_object(ANIMAL_URL, ftype='Person')

        c = Client()

        c.post('/sharedInbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "actor": HUMAN_URL,
                    "object": ANIMAL_URL,
                    "type": "Like",
                    },
                )
        return

        self.assertTrue(
                IncomingMessage.objects.all().exists())

        IncomingMessage.objects.all().delete()

        text = text[1:] # remove leading {, so the JSON is invalid

        c.post('/sharedInbox',
                content_type = 'application/activity+json',
                data = text,
                )

        self.assertFalse(
                IncomingMessage.objects.all().exists())

    @skip("broken; find out why")
    def test_all_parts_known(self):

        user = create_local_person(name="margaret")
        article = create({'type': 'Article', 'title': 'dragons'})

        IncomingMessage.objects.all().delete()

        c = Client()

        tm = test_message(
                secret = '?',
                # XXX This saves an IncomingMessage, whcih
                # is *not* what we want to do. We need to
                # have the message so we can post it via HTTP.
                )

        c.post('/users/alice/inbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "actor": user.url,
                    "object": article.url,
                    "type": "Like",
                    },
                )

        # XXX We need to deliver here

        self.assertTrue(
                Thing.objects.filter(remote_url='https://example.net/hello-world').exists())

        self.assertFalse(
                IncomingMessage.objects.all().exists())

    # XXX This creates the IncomingMessage directly, rather than
    # XXX going through the inbox, because of issue 1.
    @httpretty.activate
    def test_auto_follow(self):

        MARY_URL = 'https://altair.example.com/users/mary'
        BOB_URL = 'https://example.net/bob'
        BOB_INBOX_URL = BOB_URL+'/inbox'

        mary_keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        bob_keys = json.load(open('tests/keys/keys-0002.json', 'r'))

        mock_remote_object(BOB_URL, ftype='Person',
                content = json.dumps(remote_user(
                    name='bob',
                    url=BOB_URL,
                    publicKey=bob_keys['public'],
                    inbox=BOB_INBOX_URL,
                    sharedInbox=None,
                    )),
                )

        httpretty.register_uri(
                httpretty.POST,
                BOB_INBOX_URL,
                status=200,
                body='Thank you!',
                )

        mary = create_local_person(
                name='mary',
                auto_follow=True,
                publicKey=mary_keys['public'],
                privateKey=mary_keys['private'],
                )

        follow_request = test_message(
                secret = bob_keys['private'],
                f_id = 'https://example.net/activity/123',
                f_actor = BOB_URL,
                f_object = MARY_URL,
                f_type = "Follow",
                )
        validate(follow_request.id)

        self.assertEqual(
                httpretty.last_request().path,
                '/bob/inbox',
                )

