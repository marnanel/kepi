from django.test import TestCase, Client
from django_kepi.delivery import deliver
from django_kepi.models import Thing
from unittest.mock import Mock, patch
from . import _create_person
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

def _message_became_activity(url=ACTIVITY_ID):
    try:
        result = Thing.objects.get(remote_url=url)
        return True
    except Thing.DoesNotExist:
        return False

class ResultWrapper(object):
    def __init__(self,
            text='',
            status_code=200,
            ):
        self.text = json.dumps(text)
        self.status_code = status_code

class TestDeliverTasks(TestCase):

    def _run_delivery(
            self,
            activity_fields,
            remote_user_details,
            ):

        a = Thing.create(activity_fields)
        a.save()

        def _get(url):
            if url in remote_user_details:
                return ResultWrapper(
                        text=remote_user_details[url],
                        )
            else:
                return ResultWrapper(
                    status_code = 404,
                    )

        mock_get = Mock(
                side_effect = _get,
                )

        mock_post = Mock(
                return_value = None,
                )

        with patch('requests.get', mock_get):
            with patch('requests.post', mock_post):
                deliver(a.number)

    def test_deliver_remote(self):

        keys = json.load(open('tests/keys/keys-0000.json', 'r'))
        alice = _create_person(
                name = 'alice',
                publicKey = keys['public'],
                # XXX FIXME this is a really silly place to store the private key
                privateKey = keys['private'],
                )
        alice.save()

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': REMOTE_FRED,
                    'to': [REMOTE_FRED],
                    },
                remote_user_details = {
                    REMOTE_FRED: _remote_user(
                        url=REMOTE_FRED,
                        name='Fred',
                        sharedInbox=REMOTE_SHARED_INBOX,
                        ),
                    }
                )

    def test_deliver_local(self):

        keys0 = json.load(open('tests/keys/keys-0000.json', 'r'))
        keys1 = json.load(open('tests/keys/keys-0001.json', 'r'))
        alice = _create_person(
                name = 'alice',
                publicKey = keys0['public'],
                privateKey = keys0['private'],
                )
        alice.save()
        bob = _create_person(
                name = 'bob',
                publicKey = keys1['public'],
                privateKey = keys1['private'],
                )
        bob.save()

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': LOCAL_BOB,
                    'to': [LOCAL_BOB],
                    },
                remote_user_details = {
                    }
                )

# for investigation, rather than long-term testing
class TestBob(TestCase):
    def test_bob(self):
        alice = _create_person(
                name = 'alice',
                )
        alice.save()

        bob = _create_person(
                name = 'bob',
                )
        bob.save()

        # XXX add follower / following.
        # XXX _create_person's view is not embellishing its activity_form.

        c = Client()
        logger.info('bob %s', c.get('/users/bob').content)
        logger.info('bob friends %s', c.get('/users/bob/following').content)
        logger.info('bob friends p1 %s', c.get('/users/bob/following?page=1').content)

# This is purely about delivery, so we only use one Thing type: a Like.
# {
#    "type": "Like",
#    "actor": "alice@altair.example.com",
#    "object": "https://example.com",
#  (here: to, cc, bto, bcc, as appropriate)
# }

# These tests are all written with respect to a small group of users:
#
# Local users:
#   alice@altair.example.com
#       follows: bob, quebec, yankee
#   bob@altair.example.com
#       follows: quebec, yankee, zulu
#
# Remote users:
#   quebec@montreal.example.net
#       personal inbox: https://montreal.example.net/users/quebec
#       no shared inbox.
#       follows: alice, zulu
#
#   yankee@example.net
#       personal inbox: https://example.net/yankee
#       shared inbox: https://example.net/sharedInbox
#       follows: alice, bob
#
#   zulu@example.net
#       personal inbox: https://example.net/zulu
#       shared inbox: https://example.net/sharedInbox
#       follows: alice, bob, quebec, yankee
#
# As ever, public messages:
#   https://www.w3.org/ns/activitystreams#Public
#    (or, "as:Public", or "Public"; all three are synonyms)
#
# Generally, each test asserts that a particular set of
# inboxes were delivered to.
#
# XXX Extra: make proof against infinite recursion honeytrap.
