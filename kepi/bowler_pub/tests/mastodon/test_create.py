from django.test import TestCase
from kepi.bowler_pub.tests import create_local_note, create_local_person
from kepi.bowler_pub.create import create
from kepi.bowler_pub.models.audience import Audience, AUDIENCE_FIELD_NAMES
from kepi.bowler_pub.models.mention import Mention
from kepi.bowler_pub.models.item import AcItem
from .. import create_local_person
import logging
import json
from django.conf import settings

REMOTE_ALICE = 'https://somewhere.example.com/users/alice'
LOCAL_FRED = 'https://testserver/users/fred'

logger = logging.getLogger(name='kepi')

class TestCreate(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'
        self._fred = create_local_person(
                name = 'fred',
                )

    def _send_create_for_object(self,
            object_form,
            sender = None,
            ):

        if sender is None:
            sender = self._fred.url

        create_form = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'type': 'Create',
                'actor': sender,
                'object': object_form,
        }

        logger.info('Submitting Create activity: %s', create_form)

        activity = create(
                value = create_form,
                is_local=False)

        if activity is None:
            logger.info('  -- no activity was created')
            return None
        else:
            logger.info('  -- created activity: %s', activity)
            return activity['object__obj']

    def test_unknown_object_type(self):
        object_form = {
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
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': 'https://testserver/users/fred/followers',
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

        object_form = {
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': self._fred.id,
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

    def test_direct(self):

        object_form = {
            'type': 'Note',
            'content': 'Lorem ipsum',
            'to': LOCAL_FRED,
            'tag': {
                'type': 'Mention',
                'href': LOCAL_FRED,
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

        original_status = create_local_note(attributedTo=LOCAL_FRED)

        object_form = {
            'type': 'Note',
            'content': 'Lorem ipsum',
            'inReplyTo': original_status.id,
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
                status.in_reply_to_account_id,
                original_status.account,
                msg = 'status is a reply to the correct account',
                )

        self.assertEqual(
                status.conversation,
                original_status.conversation,
                msg = 'status is in the same conversation',
                )

    def test_with_mentions(self):

        object_form = {
            'type': 'Note',
            'content': 'Lorem ipsum',
            'tag': [
              {
                'type': 'Mention',
                'href': self._fred.id,
              },
            ],
          }

        status = self._send_create_for_object(object_form)

        self.assertIsNotNone(
                status,
                msg = 'it creates status',
                )

        self.assertIn(
                self._fred.id,
                status.mentions,
                msg = 'status mentions self._fred',
                )

    def test_with_mentions_missing_href(self):

        object_form = {
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

        from kepi.bowler_pub.models.following import Following

        local_user = create_local_person()

        following = Following(
                follower = local_user,
                following = REMOTE_ALICE,
                )
        following.save()

        object_form = {
            'type': 'Note',
            'content': 'Lorem ipsum',
          }

        status = self._send_create_for_object(object_form,
                sender=REMOTE_ALICE)

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

        local_status = create_local_note(attributedTo=LOCAL_FRED)

        object_form = {
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
            'type': 'note',
            'content': 'lorem ipsum',
          }

        status = self._send_create_for_object(object_form,
                sender = REMOTE_ALICE)

        self.assertIsNone(
                status,
                msg = 'it does not create a status',
                )
