from django.conf import settings
from django.test import TestCase, Client
import logging
import json

HOST_META_URL = 'https://altair.example.com/.well-known/host-meta'
HOST_META_MIME_TYPE = 'application/xrd+xml'

logger = logging.getLogger(name='kepi')

class TestHostMeta(TestCase):

    def test_host_meta(self):

        logger.debug('Get host-meta from %s',
                HOST_META_URL)

        settings.ALLOWED_HOSTS = [
                'altair.example.com',
                'testserver',
                ]

        client = Client()
        response = client.get(HOST_META_URL,
                HTTP_ACCEPT = HOST_META_MIME_TYPE,
                )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'],
                HOST_META_MIME_TYPE)

        self.assertIn(
                "/.well-known/webfinger?resource={uri}",
                str(response.content, encoding='UTF-8'))
