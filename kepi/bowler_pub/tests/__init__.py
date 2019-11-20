from kepi.bowler_pub.create import create
from kepi.bowler_pub.validation import IncomingMessage, validate
from kepi.bowler_pub.models import AcObject, AcActor
from kepi.bowler_pub.utils import as_json, uri_to_url, configured_url
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

LOCAL_ALICE = 'https://testserver/users/alice'
LOCAL_BOB = 'https://testserver/users/bob'

FREDS_FOLLOWERS = REMOTE_FRED+'/followers'
JIMS_FOLLOWERS = REMOTE_JIM+'/followers'
ALICES_FOLLOWERS = LOCAL_ALICE+'/followers'
BOBS_FOLLOWERS = LOCAL_BOB+'/followers'

PUBLIC = "https://www.w3.org/ns/activitystreams#Public"

CONTEXT_URL = "https://www.w3.org/ns/activitystreams"

logger = logging.getLogger(name='kepi')

def create_local_person(name='jemima',
        load_default_keys_from='kepi/bowler_pub/tests/keys/keys-0003.json',
        **kwargs):

    if 'publicKey' or 'privateKey' not in kwargs:
        keys = json.load(open(load_default_keys_from, 'r'))

        if 'publicKey' not in kwargs:
            kwargs['publicKey'] = keys['public']

        if 'privateKey' not in kwargs:
            kwargs['privateKey'] = keys['private']

    else:
        keys = None

    spec = {
        'name': name,
        'id': '@'+name,
        'type': 'Person',
        'endpoints': {
            'sharedInbox': configured_url('SHARED_INBOX_LINK'),
            },
        'inbox': configured_url('SHARED_INBOX_LINK'),
        }

    spec.update(kwargs)

    if 'publicKey' in spec:
        user_id = configured_url('USER_LINK',
            username = name,
            )
        spec['publicKey'] = {
            'id': user_id+'#main-key',
            'owner': user_id,
            'publicKeyPem': spec['publicKey'],
        }

    result = create(
            value = spec,
            run_delivery = False,
            )

    return result

def create_local_note(
        attributedTo = None,
        **kwargs):

    if isinstance(attributedTo, AcObject):
        attributedTo = attributedTo.id

    spec = {
            'type': 'Create',
            'actor': attributedTo,
            'object': {
                'type': 'Note',
                'attributedTo': attributedTo,
                'content': 'This is just a test.',
                },
            'to': [PUBLIC],
            }

    spec['object'].update(kwargs)

    result = create(**spec)
    return result['object__obj']

def create_local_like(**kwargs):

    note = create_local_note()

    spec = {
        'type': 'Like',
        'object': note.id,
        }

    spec.update(kwargs)

    result = create(**spec)
    return result

def mock_remote_object(
        url,
        content = '',
        status = 200,
        as_post = False,
        on_fetch = None,
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

    def return_body(request, url, stuff):
        logger.info('%s: fetched', url)
        if on_fetch is not None:
            on_fetch()
        return status, stuff, body

    httpretty.register_uri(
            method,
            url,
            status=status,
            headers=headers,
            body = return_body,
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
        on_fetch = None,
        **fields):

    body = as_json(
            remote_user(
                url=url,
                name=name,
                publicKey = publicKey,
                **fields,
                ))

    mock_remote_object(
            url=url,
            on_fetch=on_fetch,
            content=body,
            )

def create_remote_collection(
        url,
        items,
        number_per_page = 10,
        ):

    PAGE_URL_FORMAT = '%s?page=%d'

    mock_remote_object(
            url=url,
            content=as_json({
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
            content=as_json(fields),
            )

def test_message_body_and_headers(secret='',
        path=INBOX_PATH,
        host=INBOX_HOST,
        signed = True,
        **fields):

    body = dict([(f[2:],v) for f,v in fields.items() if f.startswith('f_')])
    body['@context'] = CONTEXT_URL
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

    if signed:

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

    if 'id' not in body:
        body['id'] = ACTIVITY_ID

    body = as_json(body)

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
            body = as_json(body),
            )

    result.save()
    return result

def post_test_message(
        secret,
        path=INBOX_PATH,
        host=INBOX_HOST,
        f_id=ACTIVITY_ID,
        client = None,
        content = None,
        **fields,
        ):

    if client is None:
        client = django.test.Client()

    body, headers = test_message_body_and_headers(
            secret = secret,
            path = path,
            host = host,
            **fields,
            )

    if content is None:
        content = body

    logger.debug("Test message is %s",
            body)
    logger.debug("  -- with headers %s",
            headers)

    response = client.post(
            path = path,
            content_type = headers['content-type'],
            data = content,
            HTTP_DATE = headers['date'],
            HTTP_HOST = headers['host'],
            HTTP_SIGNATURE = headers['signature'],
            )

    return response

def remote_user(url, name,
        publicKey='',
        inbox=None,
        sharedInbox=None,
        followers=None,
        ):
        result = {
                '@context': CONTEXT_URL,
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

def remote_object_is_recorded(url):

    from kepi.bowler_pub.models import AcObject

    try:
        result = AcObject.objects.get(id=url)
        return True
    except AcObject.DoesNotExist:
        return False
