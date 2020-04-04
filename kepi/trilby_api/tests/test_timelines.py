from django.test import TestCase, Client
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import Status
import json

MIME_TYPE = 'application/json'

class PublicTimeline(TestCase):

    # FIXME put this in a parent class in __init__
    def _get(self,
            url,
            client=None):

        if client is None:
            client = Client()

        response = client.get(url,
                HTTP_ACCEPT = MIME_TYPE,
                )

        self.assertEqual(
                response.status_code,
                200)

        return json.loads(
                str(response.content, encoding='UTF-8'))

    def test_public_empty(self):

        response = self._get('/api/v1/timelines/public')

        self.assertEqual(len(response), 0)

    def test_public_singleton(self):
        self._alice = create_local_person(name='alice')

        self._status = create_local_status(
                content = 'Hello world.',
                posted_by = self._alice,
                visibility = Status.PUBLIC,
                )

        response = self._get('/api/v1/timelines/public')

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['content'],
                '<p>Hello world.</p>',
                )

    def test_public_singleton_direct(self):
        self._alice = create_local_person(name='alice')

        self._status = create_local_status(
                content = 'Hello world.',
                posted_by = self._alice,
                visibility = Status.DIRECT,
                )

        response = self._get('/api/v1/timelines/public')

        self.assertEqual(len(response), 0)
