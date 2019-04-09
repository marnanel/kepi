import json
import httpsig
from django.test import TestCase
from django.db.models.query import QuerySet
from django_kepi.models import IncomingMessage, validate
from unittest.mock import patch
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

def _test_message(secret='', **fields):

    body = dict([(f[2:],v) for f,v in fields.items() if f.startswith('f_')])
    body['@context'] = MESSAGE_CONTEXT

    headers = {
            'content-type': "application/activity+json",
            'date': "Thu, 04 Apr 2019 21:12:11 GMT",
            'host': "europa.example.org",
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
            path='/inbox',
            )

    SIGNATURE = 'Signature'
    if headers['Authorization'].startswith(SIGNATURE):
        headers['Signature'] = headers['Authorization'][len(SIGNATURE)+1:]

    return IncomingMessage(
            content_type = headers['content-type'],
            date = headers['date'],
            digest = '', # FIXME ???
            host = headers['host'],
            signature = headers['Signature'],
            body = json.dumps(body, sort_keys=True),
            actor = body['actor'],
            key_id = key_id,
            )

class TestValidation(TestCase):

    @patch('django_kepi.validation._kick_off_background_fetch')
    @patch('django_kepi.validation.CachedPublicKey.objects.get')
    def test_local_lookup(self, mock_key_get, mock_fetch):
        
        mock_key_get.return_value = None
        keys = json.load(open('tests/keys/keys-0000.json', 'r'))

        FRED = "https://remote.example.com/users/fred"
        message = _test_message(
                f_id="https://queer.party/04b065f8-81c4-408e-bec3-9fb1f7c06408",
                f_type="Follow",
                f_actor=FRED,
                f_object="https://local.example.org/users/alice",
                secret = keys['private'],
                )
        validate(message)
        mock_fetch.assert_called_once_with(FRED)
        mock_key_get.assert_called_once_with(owner=FRED)

