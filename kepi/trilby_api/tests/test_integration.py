from django.test import TestCase
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from django.conf import settings

class TestIntegration(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def _create_alice(self):
        self._alice = create_local_person(name='alice')

    def test_post(self):

        self._create_alice()

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses',
                {
                    # This was captured from Tusky
                    "media_ids": [],
                    "sensitive": False,
                    "status": "This is a test.",
                    "visibility": "public",
                    "spoiler_text": "",
                    },
                format = 'json',
                )

        self.assertEqual(
                result.status_code,
                201, # Created
                )
        
        content = json.loads(result.content.decode())

        self.assertEqual(
                sorted([
                'id', 'uri', 'url',
                'account',
                'in_reply_to_id',
                'in_reply_to_account_id',
                'content', 'created_at',
                'emojis', 'reblogs_count',
                'favourites_count', 'reblogged',
                'favourited',
                'muted', 'sensitive',
                'spoiler_text',
                'visibility',
                'media_attachments',
                'mentions',
                'tags',
                'card',
                'poll',
                'application',
                'language',
                'pinned',
                ]),
                sorted(list(content.keys())),
                )

    def test_post_to_own_timeline(self):
        self._create_alice()

        c = APIClient()
        c.force_authenticate(self._alice.local_user)

        result = c.post(
                '/api/v1/statuses',
                {
                    # This was captured from Tusky
                    "media_ids": [],
                    "sensitive": False,
                    "status": "This should be in my inbox.",
                    "visibility": "public",
                    "spoiler_text": "",
                    },
                format = 'json',
                )

        self.assertEqual(
                result.status_code,
                201, # Created
                )

        result = c.get(
                '/api/v1/timelines/home',
                format = 'json',
                )

        self.assertEqual(
                result.status_code,
                200,
                )

        content = json.loads(result.content.decode())

        self.assertEqual(
                len(content),
                1,
                )

        self.assertEqual(
                content[0]['content'],
                '<p>This should be in my inbox.</p>',
                )
