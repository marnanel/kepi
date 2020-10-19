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
from kepi.bowler_pub.utils import as_json
from unittest import skip, expectedFailure
from django.conf import settings
import kepi.trilby_api.models as trilby_models
from kepi.bowler_pub.create import create
import httpretty

REMOTE_ALICE = 'https://somewhere.example.com/users/alice'
LOCAL_FRED = 'https://testserver/users/fred'
LOCAL_BOOST_ID = 'https://testserver/status/this-is-a-boost-id'

class Tests(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'
        self._local_fred = create_local_person(
                name = 'fred',
                )

    @httpretty.activate
    def test_sender_with_local_follower_boosts_known_status(self):
        self._remote_alice = create_remote_person(
            remote_url = REMOTE_ALICE,
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

        create(fields = boost_form)

        self.assertTrue(
                original_status.reblogged,
                msg = 'the status was reblogged at the end',
                )

    @httpretty.activate
    def test_sender_with_local_follower_boosts_unknown_status(self):
        self._remote_alice = create_remote_person(
            remote_url = REMOTE_ALICE,
            name = 'alice',
            auto_fetch = True,
            )

        follow = trilby_models.Follow(
                follower = self._local_fred,
                following = self._remote_alice,
                )
        follow.save()

        original_remote_form = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'id': 'https://example.com/actor/hello-world',
                'type': 'Note',
                'attributedTo': 'https://example.com/actor',
                'content': 'Hello world',
                'to': 'http://example.com/followers',
                }

        create_remote_person(
                remote_url = 'https://example.com/actor',
                name = 'random',
                )

        mock_remote_object(
                'https://example.com/actor/hello-world',
                as_json(
                    original_remote_form,
                    ),
                )

        boost_form = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'id': 'foo',
                'type': 'Announce',
                'actor': REMOTE_ALICE,
                'object': 'https://example.com/actor/hello-world',
                'to': 'http://example.com/followers',
        }

        create(boost_form)

        original_status = trilby_models.Status.objects.get(
                remote_url = 'https://example.com/actor/hello-world',
                )

        self.assertTrue(
                original_status.reblogged,
                msg = 'the status was reblogged at the end',
                )

        self.assertEqual(
                original_status.content,
                'Hello world',
                msg = 'the status was reblogged at the end',
                )

    def test_sender_with_local_follower_selfboosts_unknown_status(self):
        pass

    def test_reblog_of_local_status(self):
        pass

    # TODO relays are not implemented and not tested

    def test_irrelevant(self):
        pass
