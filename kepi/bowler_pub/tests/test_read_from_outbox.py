from django.conf import settings
from django.test import TestCase, Client
from kepi.bowler_pub.create import create
from . import create_local_person
import httpretty
import logging
import json

ALICE_ID = 'https://altair.example.com/users/alice'
OUTBOX = ALICE_ID+'/outbox'
OUTBOX_PATH = '/users/alice/outbox'

MIME_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'

logger = logging.getLogger(name='kepi')

VICTORIA_WOOD = {
            "type": "Create",
            "actor": "https://altair.example.com/users/alice",
            "published": "2019-07-27T13:08:46Z",
            "to": [
                "https://www.w3.org/ns/activitystreams#Public"
            ],
            "cc": [
                "https://altair.example.com/users/alice/followers"
            ],
            "object": {
                "id": "https://altair.example.com/users/alice/statuses/102513569060504404",
                "type": "Note",
                "summary": None,
                "inReplyTo": "https://altair.example.com/users/alice/statuses/102513505242530375",
                "published": "2019-07-27T13:08:46Z",
                "url": "https://altair.example.com/@marnanel/102513569060504404",
                "attributedTo": "https://altair.example.com/users/alice",
                "to": [
                    "https://www.w3.org/ns/activitystreams#Public"
                ],
                "cc": [
                    "https://altair.example.com/users/alice/followers"
                ],
                "sensitive": False,
                "conversation": "tag:altair.example.com,2019-07-27:objectId=17498957:objectType=Conversation",
                "content": "<p>Victoria Wood parodying Peter Skellern. I laughed so much at this, though you might have to know both singers&apos; work in order to find it quite as funny.</p><p>- love song<br />- self-doubt<br />- refs to northern England<br />- preamble<br />- piano solo<br />- brass band<br />- choir backing<br />- love is cosy<br />- heavy rhotic vowels</p><p><a href=\"https://youtu.be/782hqdmnq7g\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">youtu.be/782hqdmnq7g</span><span class=\"invisible\"></span></a></p>",
                "contentMap": {
                    "en": "<p>Victoria Wood parodying Peter Skellern. I laughed so much at this, though you might have to know both singers&apos; work in order to find it quite as funny.</p><p>- love song<br />- self-doubt<br />- refs to northern England<br />- preamble<br />- piano solo<br />- brass band<br />- choir backing<br />- love is cosy<br />- heavy rhotic vowels</p><p><a href=\"https://youtu.be/782hqdmnq7g\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><span class=\"\">youtu.be/782hqdmnq7g</span><span class=\"invisible\"></span></a></p>",
                },
                "attachment": [],
                "tag": [],
                "replies": {
                    "id": "https://altair.example.com/users/alice/statuses/102513569060504404/replies",
                    "type": "Collection",
                    "first": {
                        "type": "CollectionPage",
                        "partOf": "https://altair.example.com/users/alice/statuses/102513569060504404/replies",
                        "items": []
                    }
                }
            }
}

BOOST = {
        "id": "https://altair.example.com/users/alice/statuses/102513175027636695/activity",
        "type": "Announce",
        "actor": "https://altair.example.com/users/alice",
        "published": "2019-07-27T11:28:33Z",
        "to": [
            "https://www.w3.org/ns/activitystreams#Public"
            ],
        "cc": [
            "https://altair.example.com/users/alice/followers"
            ],
        "object": "https://weirder.earth.example.net/users/natrix/statuses/102504233649665656",
        "atomUri": "https://altair.example.com/users/alice/statuses/102513175027636695/activity"
        }

class TestOutbox(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    # XXX Add a boolean flag about whether to authenticate self
    def _get(self,
            url,
            client):

        response = client.get(url,
                HTTP_ACCEPT = MIME_TYPE,
                )

        self.assertEqual(
                response.status_code,
                200)

        return json.loads(
                str(response.content, encoding='UTF-8'))

    # XXX Add a boolean flag about whether to authenticate self
    def _get_collection(self, url,
            client=None):

        logger.debug('------------------')
        logger.debug('Get collection: %s', url)
        if not client:
            client = Client()

        result = []
        linkname = 'first'

        while True:
            logger.debug('  -- get page: %s', url)
            page = self._get(url, client)
            logger.debug('    -- received %s', url)

            if 'orderedItems' in page:
                result.extend(page['orderedItems'])

            if linkname not in page:
                logger.info('  -- done; collection contains: %s',
                        result)
                return result

            url = page[linkname]
            linkname = 'next'

    def _put_stuff_in_outbox(self,
            what):

        if not hasattr(self, '_example_user'):
            keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))

            alice = create_local_person(
                    name='alice',
                    publicKey=keys['public'],
                    privateKey=keys['private'],
                    )

            setattr(self, '_example_user', alice)

            settings.ALLOWED_HOSTS = [
                    'altair.example.com',
                    'testserver',
                    ]

        for thing in what:
            create(**thing)

    def test_read_empty(self):

        self._put_stuff_in_outbox([])

        contents = self._get_collection(OUTBOX)

        self.assertEqual(
                len(contents),
                0)

    def test_read_create(self):

        self._put_stuff_in_outbox([
            VICTORIA_WOOD,
            ])

        contents = self._get_collection(OUTBOX)

        self.assertEqual(
                [x['type'] for x in contents],
                ['Create'])

    def test_read_announce(self):
        # Announce, aka boost
        self._put_stuff_in_outbox([
            BOOST,
            ])

        contents = self._get_collection(OUTBOX)

        self.assertEqual(
                [x['type'] for x in contents],
                ['Announce'])
