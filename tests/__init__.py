from django_kepi.models import create
from django_kepi.validation import IncomingMessage, validate
from django_kepi.models.actor import Actor
import django.test
import httpretty
import logging
import httpsig
import json

ACTIVITY_ID = "https://example.com/04b065f8-81c4-408e-bec3-9fb1f7c06408"
INBOX_HOST = 'europa.example.com'
INBOX_PATH = '/inbox'

REMOTE_FRED = 'https://remote.example.org/users/fred'
REMOTE_JIM = 'https://remote.example.org/users/jim'

FREDS_INBOX = REMOTE_FRED+'/inbox'
JIMS_INBOX = REMOTE_JIM+'/inbox'
REMOTE_SHARED_INBOX = 'https://remote.example.org/shared-inbox'

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



logger = logging.getLogger(name='django_kepi')

def create_person(name,
        **kwargs):
    spec = {
        'name': name,
        'id': 'https://altair.example.com/users/'+name,
        'type': 'Person',
        }

    spec.update(kwargs)

    actor_fields = {}
    for extra in ['publicKey', 'privateKey']:
        if extra in spec:
            actor_fields[extra] = spec[extra]
            del spec[extra]

    result = create(spec)

    actor = Actor(
            thing=result,
            **actor_fields,
            )
    actor.save()

    return result

def mock_remote_object(
        url,
        ftype = 'Object',
        content = '',
        status = 200,
        ):

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

def test_message_body_and_headers(secret='',
        path=INBOX_PATH,
        host=INBOX_HOST,
        **fields):

    body = dict([(f[2:],v) for f,v in fields.items() if f.startswith('f_')])
    body['@context'] = MESSAGE_CONTEXT
    body['Host'] = host,

    headers = {
            'content-type': "application/activity+json",
            'date': "Thu, 04 Apr 2019 21:12:11 GMT",
            'host': host,
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
            path=path,
            )

    SIGNATURE = 'Signature'
    if headers['Authorization'].startswith(SIGNATURE):
        headers['Signature'] = headers['Authorization'][len(SIGNATURE)+1:]

    return body, headers

def test_message(secret='', **fields):

    body, headers = test_message_body_and_headers(
            secret,
            **fields,
            )

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

def post_test_message(
        path, host,
        secret,
        f_id, f_type, f_actor, f_object,
        client = None,
        ):

    if client is None:
        client = django.test.Client()

    body, headers = test_message_body_and_headers(
            f_id=f_id,
            f_type=f_type,
            f_actor=f_actor,
            f_object=f_object,
            secret = secret,
            path = path,
            host = host,
            )

    logger.debug("Test message is %s",
            body)
    logger.debug("  -- with headers %s",
            headers)

    client.post(
            path = path,
            content_type = headers['content-type'], # XXX why twice?
            data = json.dumps(body),
            CONTENT_TYPE = headers['content-type'],
            HTTP_DATE = headers['date'],
            HOST = headers['host'],
            HTTP_SIGNATURE = headers['signature'],
            )

    return client

def remote_user(url, name,
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
