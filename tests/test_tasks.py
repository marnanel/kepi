from django.test import TestCase, Client
from django_kepi.validation import IncomingMessage
from django_kepi.tasks import validate
from django_kepi.activity_model import Activity
from things_for_testing import KepiTestCase
from things_for_testing.models import ThingUser
from unittest.mock import Mock, patch
import logging
import httpretty
import httpsig
import json

logger = logging.getLogger(name='django_kepi')

POLLY_URL = 'https://remote.example.net/users/polly'
SUKI_URL = 'https://remote.example.net/services/suki/kettle'
PUT_THE_KETTLE_ON = "Let's put the kettle on"
SUKI_TAKE_IT_OFF = "Suki, take it off again"
RESULT_URL = 'https://localhost/async_result'

ACTIVITY_ID = "https://example.com/04b065f8-81c4-408e-bec3-9fb1f7c06408"
INBOX_HOST = 'europa.example.com'
INBOX_PATH = '/inbox'

REMOTE_FRED = 'https://remote.example.org/users/fred'
REMOTE_JIM = 'https://remote.example.org/users/jim'

LOCAL_ALICE = 'https://altair.example.com/users/alice'
LOCAL_BOB = 'https://altair.example.com/users/bob'

MESSAGE_CONTEXT = ["https://www.w3.org/ns/activitystreams",
        "https://w3id.org/security/v1",
        {"manuallyApprovesFollowers":"as:manuallyApprovesFollowers",
            "sensitive":"as:sensitive",
            "movedTo":{"@id":"as:movedTo",
                "@type":"@id"},
            "alsoKnownAs":{"@id":"as:alsoKnownAs",
                "@type":"@id"},
            "Hashtag":"as:Hashtag",
            "ostatus":"http://ostatus.org#",
            "atomUri":"ostatus:atomUri",
            "inReplyToAtomUri":"ostatus:inReplyToAtomUri",
            "conversation":"ostatus:conversation",
            "toot":"http://joinmastodon.org/ns#",
            "Emoji":"toot:Emoji",
            "focalPoint":{"@container":"@list",
                "@id":"toot:focalPoint"},
            "featured":{"@id":"toot:featured",
                "@type":"@id"},
            "schema":"http://schema.org#",
            "PropertyValue":"schema:PropertyValue",
            "value":"schema:value"}]

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

class TestTasks(TestCase):

    def _mock_remote_object(self,
            url,
            ftype = 'Object',
            content = '',
            status = 200):

        headers = {
                'Content-Type': 'application/activity+json',
                }

        httpretty.register_uri(
                httpretty.GET,
                url,
                status=status,
                headers=headers,
                body=bytes(content, encoding='UTF-8'))

        logger.debug('Mocking %s as %d: %s',
                url,
                status,
                content)

    def _mock_remote_service(self,
            url,
            ):

        def remote_service(request, uri, response_headers):

            self._sent_body = request.body.decode(encoding='ASCII')

            return [200, response_headers, 'Thank you.']

        self._sent_body = None

        httpretty.register_uri(
                httpretty.POST,
                url,
                body=remote_service)

    def _mock_local_endpoint(self):

        def local_endpoint(request, uri, response_headers):

            self._received_code = int(request.querystring['code'][0])
            self._received_url = request.querystring['url'][0]
            self._received_body = request.body.decode(encoding='ASCII')

            return [200, response_headers, '']

        self._received_code = None
        self._received_url = None
        self._received_body = None

        httpretty.register_uri(
                httpretty.POST,
                RESULT_URL,
                body=local_endpoint)

    @patch('requests.get')
    def test_validation(self, mock_get):
        keys = json.load(open('tests/keys/keys-0000.json', 'r'))

        alice = ThingUser(
                url = LOCAL_ALICE,
                name = 'alice',
                favourite_colour = 'puce',
                public_key = keys['public'],
                )
        alice.save()
        logger.debug('%s', alice.url)

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=LOCAL_ALICE,
                f_object=LOCAL_BOB,
                secret = keys['private'],
                )

        validate(message.id)

        try:
            result = Activity.objects.get(remote_url=ACTIVITY_ID)
        except Activity.DoesNotExist:
            result = None

        self.assertIsNotNone(result)
        mock_get.assert_not_called()

    @httpretty.activate
    def test_request_success(self):

        self._mock_remote_object(
            url = POLLY_URL,
            content = PUT_THE_KETTLE_ON,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = POLLY_URL,
                post_data = None,
                result_url = RESULT_URL,
                )

        self.assertEqual(self._received_code, 200)
        self.assertEqual(self._received_url, POLLY_URL)
        self.assertEqual(self._received_body, PUT_THE_KETTLE_ON)

    @httpretty.activate
    def test_request_failure(self):

        self._mock_remote_object(
            url = POLLY_URL,
            content = 'no idea, mate',
            status = 404,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = POLLY_URL,
                post_data = None,
                result_url = RESULT_URL,
                )

        self.assertEqual(self._received_code, 404)
        self.assertEqual(self._received_url, POLLY_URL)

    @httpretty.activate
    def test_request_gone(self):

        self._mock_remote_object(
            url = POLLY_URL,
            content = "they've all gone away",
            status = 410,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = POLLY_URL,
                post_data = None,
                result_url = RESULT_URL,
                )

        self.assertEqual(self._received_code, 410)
        self.assertEqual(self._received_url, POLLY_URL)

    @httpretty.activate
    def test_submit_success(self):

        self._mock_remote_service(
            url = SUKI_URL,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = SUKI_URL,
                post_data = SUKI_TAKE_IT_OFF,
                result_url = None,
                )

        self.assertEqual(self._sent_body, SUKI_TAKE_IT_OFF)


