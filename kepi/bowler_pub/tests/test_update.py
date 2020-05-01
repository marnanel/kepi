# test_update.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.test import TestCase
from kepi.bowler_pub.utils import configured_url
from . import create_local_person, create_remote_person, \
        create_local_note, mock_remote_object, PUBLIC
import json
import logging
import httpretty
from django.conf import settings

logger = logging.getLogger(name='kepi')

REMOTE_PERSON_ID = 'https://example.com/users/alice'
REMOTE_NOTE_ID = 'https://example.com/remote-note'
REMOTE_KEYS_FILE = 'kepi/bowler_pub/tests/keys/keys-0002.json'

ORIGINAL_CONTENT = 'Things fall apart.'
UPDATED_CONTENT = 'The centre cannot hold.'

ORIGINAL_SUMMARY = 'poetry'
UPDATED_SUMMARY = 'poetry by W H Auden'

class TestUpdate(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    @httpretty.activate
    def _test_updated_inner(self,
            as_remote,
            partial,
            ):

        logger.info("------")
        logger.info("Testing update: as_remote? %s; partial? %s",
                as_remote, partial,
                )

        if as_remote:
            keys = json.load(open(REMOTE_KEYS_FILE, 'r'))

            create_remote_person(
                    name='alice',
                    url = REMOTE_PERSON_ID,
                    publicKey = keys['public'],
                    )
            alice = find(REMOTE_PERSON_ID)

            # Alice must have a local follower;
            # otherwise, kepi will drop the incoming
            # object as irrelevant to us.
            bob = create_local_person(name='bob')
            follow = Following(follower=bob, following=REMOTE_PERSON_ID)
            follow.save()

            mock_remote_object(
                    url=REMOTE_NOTE_ID,
                    content= bytes(json.dumps({
                        'type': 'Note',
                        'attributedTo': REMOTE_PERSON_ID,
                        'content': ORIGINAL_CONTENT,
                        'to': [PUBLIC],
                        }), encoding='UTF-8')
            )

            note = find(REMOTE_NOTE_ID)
        else:
            alice = create_local_person(name='alice')
            note = create_local_note(
                    attributedTo = alice,
                    content = ORIGINAL_CONTENT,
                    )

        changes = {
                'id': note.url,
                'content': UPDATED_CONTENT,
            }

        if not partial:
            changes.update({
                'summary': UPDATED_SUMMARY,
                })

        activity = {
                'type': 'Update',
                'actor': alice.url,
                'object': changes,
                }

        result = create(
                value = activity,
                run_delivery = False,
                )
        
        note.refresh_from_db()

        self.assertEqual(
                note['content'],
                UPDATED_CONTENT,
                )

        if partial and not as_remote:
            self.assertEqual(
                    note['summary'],
                    None,
                    )
        else:
            self.assertEqual(
                    note['summary'],
                    UPDATED_SUMMARY,
                    )

    def test_updated(self):
        for as_remote in [False, True]:

            # Remote updates change the entire object;
            # local updates change only the fields named.

            for partial in [False, True]:

                self._test_updated_inner(
                        as_remote = as_remote,
                        partial = partial,
                        )
