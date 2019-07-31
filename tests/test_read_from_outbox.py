from django.test import TestCase
from django.test import Client
from . import create_local_person
import httpretty
import logging
import json

ALICE_ID = 'https://altair.example.com/users/alice'
OUTBOX = ALICE_ID+'/outbox'
OUTBOX_PATH = '/users/alice/outbox'

MIME_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'

logger = logging.getLogger(name='kepi.tests')

class TestOutbox(TestCase):

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

        if not client:
            client = Client()

        result = []
        linkname = 'first'

        while True:
            page = self._get(url, client)
            logger.debug('Received %s:', url)
            logger.debug('  -- %s', page)

            if 'orderedItems' in page:
                result.extend(page['orderedItems'])

            if linkname not in page:
                # XXX testing
                json.dump(page, open('tests/examples/current-outbox.json', 'w'),
                        indent=4)
                # XXX end testing

                logger.info('Inbox contains: %s',
                        result)
                return result

            url = page[linkname]
            linkname = 'next'

    def test_read_empty(self):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

        create_local_person(
                name='alice',
                publicKey=keys['public'],
                privateKey=keys['private'],
                )

        contents = self._get_collection(OUTBOX)

        self.assertEqual(
                len(contents),
                0)
