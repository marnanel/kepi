from django.test import TestCase
from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

MIME_TYPE = 'application/json'

# Tests for timelines. API docs are here:
# https://docs.joinmastodon.org/methods/statuses/

class TestTimelines(TestCase):

    @skip("Not yet implemented")
    def test_public(self):
        pass

    @skip("Not yet implemented")
    def test_hashtag(self):
        pass

    @skip("Not yet implemented")
    def test_home(self):
        pass

    @skip("Not yet implemented")
    def test_account_statuses(self):
        # Special case: this isn't considered a timeline method
        # in the API, but it's similar enough that we test it here
        pass

    @skip("Not yet implemented")
    def test_list(self):
        pass

######################################

# TODO: Pre-existing code, to merge

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
                'Hello world.',
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
