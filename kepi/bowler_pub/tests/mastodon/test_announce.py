# test_announce.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

from django.test import TestCase
from kepi.bowler_pub.tests import *
from kepi.trilby_api.tests import create_local_person, create_local_status
from unittest import skip, expectedFailure
from django.conf import settings
import kepi.trilby_api.models as trilby_models
from kepi.bowler_pub.create import create
import httpretty

REMOTE_ALICE = 'https://somewhere.example.com/users/alice'
LOCAL_FRED = 'https://testserver/users/fred'
LOCAL_BOOST_ID = 'https://testserver/status/this-is-a-boost-id'

class TestAnnounce(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'
        self._local_fred = create_local_person(
                name = 'fred',
                )

    @httpretty.activate
    def test_sender_with_local_follower_boosts_known_status(self):
        self._remote_alice = create_remote_person(
            url = REMOTE_ALICE,
            name = 'alice',
            auto_fetch = True,
            )

        follow = trilby_models.Follow(
                follower = self._local_fred,
                following = self._remote_alice,
                )
        follow.save()

        original_status = create_local_status(
                posted_by=self._local_fred,
                )

        self.assertFalse(
                original_status.reblogged,
                msg = 'the status was not reblogged at the start',
                )

        boost_form = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'id': 'foo',
                'type': 'Announce',
                'actor': REMOTE_ALICE,
                'object': original_status.url,
                'to': 'http://example.com/followers',
        }

        message = DummyMessage(boost_form)

        create(message)

        self.assertTrue(
                original_status.reblogged,
                msg = 'the status was reblogged at the end',
                )

    def test_sender_with_local_follower_boosts_unknown_status(self):
        pass

    def test_sender_with_local_follower_selfboosts_unknown_status(self):
        pass

    def test_reblog_of_local_status(self):
        pass

    # TODO relays are not implemented and not tested

    def test_irrelevant(self):
        pass
