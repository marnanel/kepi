from django.test import TestCase, Client
from django_kepi.validation import IncomingMessage
from django_kepi.tasks import validate, deliver
from django_kepi.activity_model import Activity
from things_for_testing import KepiTestCase
from things_for_testing.models import ThingUser
from unittest.mock import Mock, patch
import logging
import httpsig
import json

# FIXME test caching
# FIXME test invalid keys

logger = logging.getLogger(name='django_kepi')

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

def _remote_user(url, name, public_key):
        result = {
                '@context': MESSAGE_CONTEXT,
                'id': url,
                'type': 'Person',
                'following': '',
                'followers': '',
                'inbox': '',
                'outbox': '',
                'featured': '',
                'preferredUsername': name,
                'url': url,
                'publicKey': {
                    'id': url+'#main-key',
                    'owner': url,
                    'publicKeyPem': public_key,
                    },
                }
        return result

def _message_became_activity(url=ACTIVITY_ID):
    try:
        result = Activity.objects.get(remote_url=url)
        return True
    except Activity.DoesNotExist:
        return False

class ResultWrapper(object):
    def __init__(self,
            text='',
            status_code=200,
            ):
        self.text = json.dumps(text)
        self.status_code = status_code

class TestValidationTasks(TestCase):

    @patch('requests.get')
    def test_local_lookup(self, mock_get):
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

        self.assertTrue(_message_became_activity())
        mock_get.assert_not_called()

    @patch('requests.get')
    def test_remote_user_known(self, mock_get):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        mock_get.return_value = ResultWrapper(
                text = _remote_user(
                    url = REMOTE_FRED,
                    name = 'Fred',
                    public_key=keys['public']),
                )

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )
        validate(message.id)

        self.assertTrue(_message_became_activity())
        mock_get.assert_called_once_with(REMOTE_FRED)

    @patch('requests.get')
    def test_remote_user_spoofed(self, mock_get):
        keys1 = json.load(open('tests/keys/keys-0001.json', 'r'))
        keys2 = json.load(open('tests/keys/keys-0002.json', 'r'))
        mock_get.return_value = ResultWrapper(
                text = _remote_user(
                    url = REMOTE_FRED,
                    name = 'Fred',
                    public_key=keys2['public'],
                ))

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys1['private'],
                )
        validate(message.id)

        self.assertFalse(_message_became_activity())

        mock_get.assert_called_once_with(REMOTE_FRED)

    @patch('requests.get')
    def test_remote_user_gone(self, mock_get):
        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        mock_get.return_value = ResultWrapper(
                status_code = 410,
                )

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )
        validate(message.id)

        self.assertFalse(_message_became_activity())

        mock_get.assert_called_once_with(REMOTE_FRED)

    @patch('requests.get')
    def test_remote_user_unknown(self, mock_get):
        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        mock_get.return_value = ResultWrapper(
                status_code = 404,
                )

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )
        validate(message.id)

        self.assertFalse(_message_became_activity())

        mock_get.assert_called_once_with(REMOTE_FRED)

class TestDeliverTasks(TestCase):

    def _run_delivery(
            self,
            activity_fields,
            ):

        a = Activity.create(activity_fields)
        a.save()

        mock_get = Mock(
                return_value = ResultWrapper(
                    status_code = 404,
                    ),
                )

        mock_post = Mock(
                return_value = None,
                )

        with patch('requests.get', mock_get):
            with patch('requests.post', mock_post):
                deliver(a.uuid)

    def test_deliver(self):

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': REMOTE_FRED,
                    'to': [REMOTE_FRED],
                    },
                )
