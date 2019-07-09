from django.test import TestCase
from tests import create_local_note, create_local_person
from django_kepi.create import create
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.mention import Mention
from django_kepi.models.item import Item
import logging
import json

SENDER_ID = 'https://example.com/actor'
SENDER_DOMAIN = 'example.com'
SENDER_FOLLOWERS = 'https://example.com/followers'

RECIPIENT_ID = 'https://altair.example.com/users/fred'

logger = logging.getLogger(name='django_kepi')

class TestCreate(TestCase):

    def _send_create_for_object(self,
            object_form):

        create_form = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'id': SENDER_ID + '#foo',
                'type': 'Create',
                'actor': SENDER_ID,
                'object': object_form,
        }

        logger.info('Submitting Create activity: %s', create_form)

        activity = create(**create_form,
                is_local=False)

        logger.info('Created activity: %s', activity)

        statuses = Item.objects.filter(
                f_attributedTo=json.dumps(SENDER_ID),
                )

        try:
            result = statuses[0]
        except IndexError:
            result = None

        logger.info('New status: %s', result)

        return result

    def test_unknown_object_type(self):
        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Banana',
            'content': 'Lorem ipsum',
          }

        status = self._send_create_for_object(object_form)

        self.assertIsNone(
                status,
                msg = 'it does not create a status',
                )

    def test_standalone(self):
        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
          }

        status = self._send_create_for_object(object_form)

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
        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': 'https://www.w3.org/ns/activitystreams#Public',
          }

        status = self._send_create_for_object(object_form)

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
        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'cc': 'https://www.w3.org/ns/activitystreams#Public',
          }

        status = self._send_create_for_object(object_form)

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
        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': 'http://example.com/followers',
          }

        status = self._send_create_for_object(object_form)

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

        recipient = create_local_person()

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': recipient,
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': RECIPIENT_ID,
            'tag': {
                'type': 'Mention',
                'href': RECIPIENT_ID,
                },
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'inReplyTo': original_status,
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
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

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'tag': [
              {
                'type': 'Mention',
              },
            ],
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'inReplyTo': local_status.id,
          }

        status = status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': local_user.id,
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'note',
            'content': 'lorem ipsum',
            'cc': local_user.id,
          }

        status = self._send_create_for_object(object_form)

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

        object_form = {
            'id': SENDER_ID + '#bar',
            'type': 'note',
            'content': 'lorem ipsum',
            'cc': local_user.id,
          }

        status = self._send_create_for_object(object_form)

        self.assertEqual(
                Thing.objects.count(),
                0,
                msg = 'it does not create a status',
                )
