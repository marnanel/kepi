from kepi.bowler_pub.validation import validate
from kepi.bowler_pub.models import Incoming
import kepi.trilby_api.models as trilby_models
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

class DummyMessage(object):

    fields = None

    def __init__(self, fields=None):
        self.fields = fields

    def __str__(self):
        return 'test message'

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
        on_fetch = None,
        auto_fetch = False,
        load_default_keys_from='kepi/bowler_pub/tests/keys/keys-0002.json',
        **fields):

    """
    Mock a remote user.

    Parameters:
        url: the URL representing this user
        name: the user's name (their "preferredUsername")
        on_fetch: an optional callback for when someone
            fetches the user's details
        auto_fetch: if True, after creation we immediately
            fetch the new remote person and return its
            RemotePerson value. If False (the default), we
            only mock the user, not updating RemotePerson
            at all, and return None.
        load_default_keys_from: the filename for the default
            public and private keys. Probably best to
            leave this alone.

        Any other named parameters will be used to populate the
        JSON for the remote user.

    If you use this function, you must decorate your test with
    @httpretty.activate .
    """

    if 'publicKey' not in fields:
        keys = json.load(open(load_default_keys_from, 'r'))

        fields['publicKey'] = keys['public']

    body = as_json(
            remote_user(
                url=url,
                name=name,
                **fields,
                ))

    mock_remote_object(
            url=url,
            on_fetch=on_fetch,
            content=body,
            )

    if auto_fetch:
        from kepi.sombrero_sendpub.fetch import fetch

        return fetch(url,
                expected_type=trilby_models.RemotePerson)
    else:
        return None

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
        fields = {},
        ):

    body = fields.copy()
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
        # the only reason "actor" would be missing from body
        # is if we're deliberately messing around with the body
        # but we still need the headers. In that case it's
        # not a problem for the test value of the key name
        # to be "#main-key".
        key_id = body.get('actor', '')+'#main-key'

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

def test_message(secret='', fields={}):

    body, headers = test_message_body_and_headers(
            secret = secret,
            fields = fields,
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
        client = None,
        content = None,
        fields = {},
        ):

    if client is None:
        client = django.test.Client()

    body, headers = test_message_body_and_headers(
            secret = secret,
            path = path,
            host = host,
            fields = fields,
            )

    if content is None:
        content = body

    logger.debug("Test message is %s",
            content)
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
        sharedInbox=None,
        ):
        result = {
                '@context': CONTEXT_URL,
                'id': url,
                'type': 'Person',
                'following': url+"/following",
                'followers': url+"/followers",
                'inbox': url+"/inbox",
                'outbox': url+"/outbox",
                'featured': url+"/collections/featured",
                'preferredUsername': name,
                'url': url,
                'publicKey': {
                    'id': url+'#main-key',
                    'owner': url,
                    'publicKeyPem': publicKey,
                    },
                }

        if sharedInbox is not None:
            result['endpoints'] = {
                    'sharedInbox': sharedInbox,
                    }

        return result
