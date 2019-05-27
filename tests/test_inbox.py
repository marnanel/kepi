from django.test import TestCase, Client
from django_kepi.views import InboxView
from django_kepi.models import Thing, create
from django_kepi.validation import IncomingMessage
from unittest import skip
from . import *
import json
import httpretty
import logging

logger = logging.getLogger(name='django_kepi')

#@skip("none of these tests sign their messages, so they all fail")
class TestInbox(TestCase):

    @httpretty.activate
    def test_specific_post(self):

        HUMAN_URL = 'https://users.example.net/mary'
        ANIMAL_URL = 'https://things.example.org/lamb'

        mock_remote_object(HUMAN_URL, ftype='Person')
        mock_remote_object(ANIMAL_URL, ftype='Person')

        c = Client()

        c.post('/users/alice/inbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "actor": HUMAN_URL,
                    "object": ANIMAL_URL,
                    "type": "Like",
                    },
                )

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

        user = create_person(name="margaret")
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

def _test_message(secret='', **fields):

    body = dict([(f[2:],v) for f,v in fields.items() if f.startswith('f_')])
    body['@context'] = MESSAGE_CONTEXT
    body['Host'] = INBOX_HOST

    headers = {
            'content-type': "application/activity+json",
            'date': "Thu, 04 Apr 2019 21:12:11 GMT",
            'host': INBOX_HOST,
            }

    if 'key_id' in fields:
        key_id = fields['key_id']
    else:
        key_id = body['actor']+'#main-key'

    signer = httpsig.HeaderSigner(
            secret=secret,
            algorithm='rsa-sha256',
            key_id = key_id,
            headers=['(request-target)', 'host', 'date', 'content-type'],
            )

    headers = signer.sign(
            headers,
            method='POST',
            path=INBOX_PATH,
            )

    SIGNATURE = 'Signature'
    if headers['Authorization'].startswith(SIGNATURE):
        headers['Signature'] = headers['Authorization'][len(SIGNATURE)+1:]

    result = IncomingMessage(
            content_type = headers['content-type'],
            date = headers['date'],
            digest = '', # FIXME ???
            host = headers['host'],
            path = INBOX_PATH,
            signature = headers['Signature'],
            body = json.dumps(body, sort_keys=True),
            )

    result.save()
    return result

def _remote_user(url, name,
        publicKey='',
        inbox=None,
        sharedInbox=None,
        ):
        result = {
                '@context': MESSAGE_CONTEXT,
                'id': url,
                'type': 'Person',
                'following': '',
                'followers': '',
                'outbox': '',
                'featured': '',
                'preferredUsername': name,
                'url': url,
                'publicKey': {
                    'id': url+'#main-key',
                    'owner': url,
                    'publicKeyPem': publicKey,
                    },
                }

        if inbox is not None:
            result['inbox'] = inbox

        if sharedInbox is not None:
            result['endpoints'] = {
                    'sharedInbox': sharedInbox,
                    }

        return result


