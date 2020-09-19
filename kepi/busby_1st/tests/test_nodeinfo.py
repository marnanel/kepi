from django.conf import settings
from django.test import TestCase, Client
import logging
import json

NODEINFO_PART_1_URL = 'http://testserver/.well-known/nodeinfo'
NODEINFO_PART_2_URL = 'http://testserver/nodeinfo.json'
MIME_TYPE = 'application/json; profile=http://nodeinfo.diaspora.software/ns/schema/2.0#'

logger = logging.getLogger(name='kepi')

class TestNodeinfo(TestCase):

    def setUp(self):
        settings.ALLOWED_HOSTS = [
                'testserver',
                ]

    def test_part_1(self):

        logger.debug('Get nodeinfo from %s',
                NODEINFO_PART_1_URL)

        client = Client()
        response = client.get(NODEINFO_PART_1_URL,
                HTTP_ACCEPT = MIME_TYPE,
                )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'],
                MIME_TYPE)

        response = json.loads(response.content)

        self.assertIn(
                "links",
                response)

        self.assertIn(
                {
                    "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                    "href": NODEINFO_PART_2_URL,
                    },
                response['links'],
                )

    def test_part_2(self):

        logger.debug('Get nodeinfo part 2 from %s',
                NODEINFO_PART_2_URL)

        client = Client()
        response = client.get(NODEINFO_PART_2_URL,
                HTTP_ACCEPT = MIME_TYPE,
                )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'],
                MIME_TYPE)

        response = json.loads(response.content)

        self.assertEqual(
            response['version'],
            "2.0",
            )

        self.assertEqual(
            response['software']['name'],
            'kepi',
            )

        self.assertIn(
                'activitypub',
                response['protocols'],
                )
