import json
import httpsig
from django.test import TestCase
from django.db.models.query import QuerySet
from django_kepi.models import IncomingMessage, validate
from unittest.mock import Mock, patch
import django_kepi.validation

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

ACTIVITY_ID = "https://example.com/04b065f8-81c4-408e-bec3-9fb1f7c06408"
INBOX_HOST = 'europa.example.com'
INBOX_PATH = '/inbox'

REMOTE_FRED = 'https://remote.example.org/users/fred'
REMOTE_JIM = 'https://remote.example.org/users/jim'

LOCAL_ALICE = 'https://altair.example.com/alice'
LOCAL_BOB = 'https://altair.example.com/bob'

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

    return IncomingMessage(
            content_type = headers['content-type'],
            date = headers['date'],
            digest = '', # FIXME ???
            host = headers['host'],
            path = INBOX_PATH,
            signature = headers['Signature'],
            body = json.dumps(body, sort_keys=True),
            )

@patch('django_kepi.validation.find')
@patch('django_kepi.validation._kick_off_background_fetch')
@patch('django_kepi.validation.CachedRemoteUser.objects.get')
class TestValidation(TestCase):

    def test_local_lookup(self, mock_key_get, mock_fetch, mock_find):
        
        keys = json.load(open('tests/keys/keys-0000.json', 'r'))
        mock_find.return_value = Mock()
        mock_find.return_value.key = keys['public']

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=LOCAL_ALICE,
                f_object=LOCAL_BOB,
                secret = keys['private'],
                )

        validate(message)

        mock_find.assert_called_once_with(LOCAL_ALICE, 'Actor')
        mock_fetch.assert_not_called()
        mock_key_get.assert_not_called()

    def test_remote_user_known(self, mock_key_get, mock_fetch, mock_find):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))
        mock_key_get.return_value = django_kepi.validation.CachedRemoteUser(
                key=keys['public'])

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_FRED,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )
        validate(message)

        mock_find.assert_not_called()
        mock_fetch.assert_not_called()
        mock_key_get.assert_called_once_with(owner=REMOTE_FRED)

    def test_remote_user_gone(self, mock_key_get, mock_fetch, mock_find):

        keys = json.load(open('tests/keys/keys-0002.json', 'r'))
        mock_key_get.return_value = django_kepi.validation.CachedRemoteUser(
                key=None)

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_JIM,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )
        validate(message)

        mock_find.assert_not_called()
        mock_fetch.assert_not_called()
        mock_key_get.assert_called_once_with(owner=REMOTE_JIM)

    def test_remote_user_spoofed(self, mock_key_get, mock_fetch, mock_find):

        keys = json.load(open('tests/keys/keys-0002.json', 'r'))
        mock_key_get.return_value = None

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_JIM,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                key_id = REMOTE_FRED+'#main-key',
                )
        validate(message)

        mock_find.assert_not_called()
        mock_fetch.assert_not_called()
        mock_key_get.assert_not_called()

    def test_remote_user_unknown(self, mock_key_get, mock_fetch, mock_find):

        keys = json.load(open('tests/keys/keys-0002.json', 'r'))
        mock_key_get.return_value = None

        message = _test_message(
                f_id=ACTIVITY_ID,
                f_type="Follow",
                f_actor=REMOTE_JIM,
                f_object=LOCAL_ALICE,
                secret = keys['private'],
                )
        validate(message)

        mock_find.assert_not_called()
        mock_fetch.assert_called_once_with(REMOTE_JIM)
        mock_key_get.assert_called_once_with(owner=REMOTE_JIM)

