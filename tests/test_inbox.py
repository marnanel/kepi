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
    def _post_to_inbox(self,
            local_inbox_path):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        create_local_person(
                name='alice',
                auto_follow=False,
                )

        create_remote_person(
                name='fred',
                url=REMOTE_FRED,
                publicKey = keys['public'],
                )

        post_test_message(
            path = local_inbox_path,
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
    def test_specific_post(self):
        self._post_to_inbox('/users/alice/inbox')

    @httpretty.activate
    def test_shared_post(self):
        self._post_to_inbox(INBOX_PATH)

    def test_non_json(self):
        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        body, headers = test_message_body_and_headers(
                f_actor = REMOTE_FRED,
                secret = keys['private'],
                )
        # we don't use the body it gives us

        c = Client()
        result = c.post(
                path = INBOX_PATH,
                content_type = 'text/plain',
                data = 'Hello',
                HTTP_DATE = headers['date'],
                HOST = headers['host'],
                HTTP_SIGNATURE = headers['signature'],
                )

        self.assertEqual(
                result.status_code,
                415, # unsupported media type
                )

        self.assertFalse(
                IncomingMessage.objects.all().exists())

    def test_malformed_json(self):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        body, headers = test_message_body_and_headers(
                f_actor = REMOTE_FRED,
                secret = keys['private'],
                )
        # we don't use the body it returns

        broken_json = json.dumps(body)[1:]

        c = Client()
        result = c.post(
                path = INBOX_PATH,
                content_type = headers['content-type'],
                data = broken_json,
                HTTP_DATE = headers['date'],
                HOST = headers['host'],
                HTTP_SIGNATURE = headers['signature'],
                )

        self.assertEqual(
                result.status_code,
                415, # unsupported media type
                )

        self.assertFalse(
                IncomingMessage.objects.all().exists())

    def test_invalid_utf8(self):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        body, headers = test_message_body_and_headers(
                f_actor = REMOTE_FRED,
                secret = keys['private'],
                )
        # we don't use the body it returns

        invalid_utf8 = b"\xa0\xa1"

        c = Client()
        result = c.post(
                path = INBOX_PATH,
                content_type = headers['content-type'],
                data = invalid_utf8,
                HTTP_DATE = headers['date'],
                HOST = headers['host'],
                HTTP_SIGNATURE = headers['signature'],
                )

        self.assertEqual(
                result.status_code,
                400, # bad request
                )

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

