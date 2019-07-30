from django_kepi.create import create
from django_kepi.validation import IncomingMessage, validate
from django_kepi.models.actor import Actor
from django.conf import settings
import django.test
import httpretty
import logging
import httpsig
import json

ACTIVITY_ID = "https://example.com/04b065f8-81c4-408e-bec3-9fb1f7c06408"
ACTIVITY_DATE = "Thu, 04 Apr 2019 21:12:11 GMT"
INBOX_HOST = 'europa.example.com'
INBOX_PATH = '/sharedInbox'

REMOTE_FRED = 'https://remote.example.org/users/fred'
REMOTE_JIM = 'https://remote.example.org/users/jim'

FREDS_INBOX = REMOTE_FRED+'/inbox'
JIMS_INBOX = REMOTE_JIM+'/inbox'
REMOTE_SHARED_INBOX = 'https://remote.example.org/shared-inbox'

LOCAL_ALICE = 'https://altair.example.com/users/alice'
LOCAL_BOB = 'https://altair.example.com/users/bob'

FREDS_FOLLOWERS = REMOTE_FRED+'/followers'
JIMS_FOLLOWERS = REMOTE_JIM+'/followers'
ALICES_FOLLOWERS = LOCAL_ALICE+'/followers'
BOBS_FOLLOWERS = LOCAL_BOB+'/followers'

PUBLIC = "https://www.w3.org/ns/activitystreams#Public"

CONTEXT_URL = "https://www.w3.org/ns/activitystreams"
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

def create_local_person(name='jemima',
        **kwargs):
    spec = {
        'name': name,
        'preferredUsername': name,
        'id': settings.KEPI['USER_URL_FORMAT'] % (name),
        'type': 'Person',
        'endpoints': {'sharedInbox': settings.KEPI['SHARED_INBOX']},
        'inbox': settings.KEPI['SHARED_INBOX'],
        }

    spec.update(kwargs)

    if 'publicKey' in spec:
        spec['publicKey'] = {
            'id': spec['id']+'#main-key',
            'owner': spec['id'],
            'publicKeyPem': spec['publicKey'],
        }

    result = create(**spec)

    return result

def create_local_note(**kwargs):
    spec = {
        'id': 'https://altair.example.com/testing-note',
        'type': 'Note',
        'content': 'This is just a test.',
        }

    spec.update(kwargs)

    result = create(**spec)
    return result

def mock_remote_object(
        url,
        ftype = 'Object',
        content = '',
        status = 200,
        as_post = False,
        ):

    headers = {
            'Content-Type': 'application/activity+json',
            }

    if isinstance(content, bytes):
        body = content
    else:
        body = bytes(content, encoding='UTF-8')

    if as_post:
        method = httpretty.POST
    else:
        method = httpretty.GET

    httpretty.register_uri(
            method,
            url,
            status=status,
            headers=headers,
            body = body,
            match_querystring = True,
            )

    logger.debug('Mocking %s as %d: %s',
            url,
            status,
            content)

def create_remote_person(
        url,
        name,
        publicKey,
        **fields):

    mock_remote_object(
            url=url,
            content=json.dumps(remote_user(
                url=url,
                name=name,
                publicKey = publicKey,
                **fields,
                )),
            )

def create_remote_collection(
        url,
        items,
        number_per_page = 10,
        ):

    PAGE_URL_FORMAT = '%s?page=%d'

    mock_remote_object(
            url=url,
            content=json.dumps({
                    "@context" : "https://www.w3.org/ns/activitystreams",
                    "id" : url,
                    "type" : "OrderedCollection",
                    "totalItems" : len(items),
                    "first" : PAGE_URL_FORMAT % (url, 1),
                    }),
                )

    page_count = len(items)//number_per_page
    for i in range(1, page_count+2):

        fields = {
                "@context" : CONTEXT_URL,
                "id" : PAGE_URL_FORMAT % (url, i),
                "type" : "OrderedCollectionPage",
                "totalItems" : len(items),
                "partOf": url,
                "orderedItems": items[(i-1)*number_per_page:i*number_per_page],
            }

        if i>1:
            fields['prev'] = PAGE_URL_FORMAT % (url, i-1)

        if i<page_count+1:
            fields['next'] = PAGE_URL_FORMAT % (url, i+1)

        mock_remote_object(
            url = PAGE_URL_FORMAT % (url, i),
            content=json.dumps(fields),
            )

def test_message_body_and_headers(secret='',
        path=INBOX_PATH,
        host=INBOX_HOST,
        signed = True,
        **fields):

    body = dict([(f[2:],v) for f,v in fields.items() if f.startswith('f_')])
    body['@context'] = MESSAGE_CONTEXT
    body['Host'] = host

    headers = {
            'content-type': "application/activity+json",
            'date': ACTIVITY_DATE,
            'host': host,
            }

    if 'key_id' in fields:
        key_id = fields['key_id']
    else:
        key_id = body['actor']+'#main-key'

    if not signed:
        return body, headers

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
        secret,
        f_type, f_actor, f_object,
        path=INBOX_PATH,
        host=INBOX_HOST,
        f_id=ACTIVITY_ID,
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
            content_type = headers['content-type'],
            data = json.dumps(body),
            HTTP_DATE = headers['date'],
            HOST = headers['host'],
            HTTP_SIGNATURE = headers['signature'],
            )

    return client

def remote_user(url, name,
        publicKey='',
        inbox=None,
        sharedInbox=None,
        followers=None,
        ):
        result = {
                '@context': MESSAGE_CONTEXT,
                'id': url,
                'type': 'Person',
                'following': '',
                'followers': followers,
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
