from django.test import TestCase
from tests import create_local_note, create_local_person
from django_kepi.models import create, Thing
import logging

SENDER_ID = 'https://example.com/actor'
SENDER_DOMAIN = 'example.com'
SENDER_FOLLOWERS = 'https://example.com/followers'

logger = logging.getLogger(name='tests')

# nb: the Mastodon tests generally check creation by
# requesting the most recent status for the sender;
# our interface doesn't make that easy at present.
# When it does, rewrite those parts. FIXME.

class TestCreate(TestCase):

    def test_unknown_object_type(self):

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Banana',
            'content': 'Lorem ipsum',
          }

        status = create(**object_json)

        self.assertEqual(
                Thing.objects.count(),
                0,
                msg = 'it does not create a status',
                )

    def test_standalone(self):
        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

        self.assertEqual(
                status.visibility,
                'direct',
                msg = 'missing to/cc defaults to direct privacy',
                )

    def test_public(self):
        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': 'https://www.w3.org/ns/activitystreams#Public',
          }

        status = status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

        self.assertEqual(
                status.visibility,
                'public',
                msg = 'status is public',
                )

    def test_unlisted(self):
        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'cc': 'https://www.w3.org/ns/activitystreams#Public',
          }

        status = status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

        self.assertEqual(
                status.visibility,
                'unlisted',
                msg = 'status is unlisted',
                )

    def test_private(self):
        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': 'http://example.com/followers',
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

        self.assertEqual(
                status.visibility,
                'private',
                msg = 'status is private',
                )

    def test_limited(self):
        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': RECIPIENT_ID,
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.visibility,
                'limited',
                msg = 'status is limited',
                )

        self.assertEqual(
                status.is_silent,
                True,
                msg = 'status is silent',
                )

    def test_direct(self):

        recipient = create_local_person()

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': RECIPIENT_ID,
            'tag': {
                'type': 'Mention',
                'href': RECIPIENT_ID,
                },
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.visibility,
                'direct',
                msg = 'status is direct',
                )

    def test_as_reply(self):

        original_status = create_local_note()

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'inReplyTo': original_status,
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.thread,
                original_status,
                msg = 'status is in the thread',
                )

        self.assertEqual(
                status.is_reply,
                True,
                msg = 'status is a reply',
                )

        self.assertEqual(
                status.in_reply_to_account,
                original_status.account,
                msg = 'status is a reply to the correct account',
                )

        self.assertEqual(
                status.conversation,
                original_status.conversation,
                msg = 'status is in the same conversation',
                )

    def test_with_mentions(self):

        recipient = create_local_person()

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'tag': [
              {
                'type': 'Mention',
                'href': recipient.id,
              },
            ],
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertIn(
                recipient.id,
                status.mentions,
                msg = 'status mentions recipient',
                )

    def test_with_mentions_missing_href(self):

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'tag': [
              {
                'type': 'Mention',
              },
            ],
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

    # For the time being, ignoring tests for:
    #   - media
    #   - hashtags
    #   - emoji
    #   - polls

    def test_when_sender_is_followed_by_local_users(self):

        local_user = create_local_person()

        following = Following(
                follower = local_user,
                following = SENDER_ID,
                )
        following.save()

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

    def test_when_sender_replies_to_local_status(self):

        local_status = create_local_note()

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'inReplyTo': local_status.id,
          }

        status = status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

    def test_when_sender_targets_a_local_user(self):

        local_user = create_local_person()

        object_json = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': local_user.id,
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'Lorem ipsum',
                msg = 'it creates status text',
                )

    def test_when_sender_ccs_a_local_user(self):

        local_user = create_local_person()

        object_json = {
            'id': sender_id + '#bar',
            'type': 'note',
            'content': 'lorem ipsum',
            'cc': local_user.id,
          }

        status = create(**object_json)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertEqual(
                status.text,
                'lorem ipsum',
                msg = 'it creates status text',
                )

    def test_when_sender_has_no_relevance_to_local_activity(self):

        local_user = create_local_person()

        object_json = {
            'id': sender_id + '#bar',
            'type': 'note',
            'content': 'lorem ipsum',
            'cc': local_user.id,
          }

        status = create(**object_json)

        self.assertEqual(
                Thing.objects.count(),
                0,
                msg = 'it does not create a status',
                )
