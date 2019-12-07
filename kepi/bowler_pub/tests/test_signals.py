# test_signals.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.test import TestCase
from kepi.bowler_pub.create import create
from kepi.bowler_pub.find import find
from kepi.bowler_pub.signals import created, updated, deleted
from kepi.bowler_pub.utils import configured_url
from kepi.bowler_pub.models.acobject import AcObject
from kepi.bowler_pub.models.following import Following
from . import create_local_person, create_remote_person, \
        create_local_note, mock_remote_object, PUBLIC
import json
import httpretty
from django.conf import settings

ORIGINAL_CONTENT = 'Share and enjoy!'
UPDATED_CONTENT = 'Go stick your head in a pig!'

class TestSignals(TestCase):

    def test_created(self):

        self._signal_was_called_with = None
        
        def receiver(sender, value, **kwargs):
            self._signal_was_called_with = value

        created.connect(receiver)

        arthur = create_local_person(name='arthur')

        self.assertEqual(
                self._signal_was_called_with,
                arthur,
                )

    def test_updated(self):

        self._signal_was_called_with = None

        def receiver(sender, value, **kwargs):
            self._signal_was_called_with = value

        updated.connect(receiver)

        arthur = create_local_person(name='arthur')
        note = create_local_note(
                attributedTo = arthur,
                content = ORIGINAL_CONTENT,
                )

        self.assertEqual(
                self._signal_was_called_with,
                None,
                )

        changes = {
                'id': note.url,
                'content': UPDATED_CONTENT,
            }

        activity = {
                'type': 'Update',
                'actor': arthur.url,
                'object': changes,
                }

        result = create(
                value = activity,
                run_delivery = False,
                )

        note.refresh_from_db()

        self.assertEqual(
                self._signal_was_called_with,
                note,
                )

        self.assertEqual(
                note['content'],
                UPDATED_CONTENT,
                )

    def test_deleted(self):

        self._signal_was_called_with = None

        def receiver(sender, url, entombed, **kwargs):
            self._signal_was_called_with = url

        deleted.connect(receiver)

        arthur = create_local_person(name='arthur')
        note = create_local_note(
                attributedTo = arthur,
                content = 'Fatuous sort of thing to say, really.',
                )

        note_url = note.url

        self.assertEqual(
                self._signal_was_called_with,
                None,
                )

        activity = {
                'type': 'Delete',
                'actor': arthur.url,
                'object': note_url,
                }

        result = create(
                value = activity,
                run_delivery = False,
                )

        self.assertEqual(
                self._signal_was_called_with,
                note_url,
                )

