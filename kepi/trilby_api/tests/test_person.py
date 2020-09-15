# test_person.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from kepi.trilby_api.tests import *
from kepi.bowler_pub.tests import create_remote_person, mock_remote_object
from unittest import skip
from rest_framework.test import APIClient, force_authenticate
import logging
import httpretty

logger = logging.getLogger(name='kepi')

REMOTE_FOLLOWERS_COLLECTION = """{
"@context":"https://www.w3.org/ns/activitystreams",
"id":"https://example.com/users/peter/followers",
"type":"OrderedCollection",
"totalItems":3,
"orderedItems": [
"https://example.com/users/quentin",
"https://example.com/users/roger",
"https://testserver/users/alice",
"https://testserver/users/bob"
]}"""

# This needs expanding into a full unit test.

class TestPerson(TrilbyTestCase):

    @httpretty.activate
    def test_followers(self):

        alice = create_local_person(name='alice')
        bob = create_local_person(name='bob')
        carol = create_local_person(name='carol')

        peter = create_remote_person(
                url = "https://example.com/users/peter",
                name = "peter",
                auto_fetch = True,
                )
        quentin = create_remote_person(
                url = "https://example.com/users/quentin",
                name = "quentin",
                auto_fetch = True,
                )
        roger = create_remote_person(
                url = "https://example.com/users/roger",
                name = "roger",
                auto_fetch = True,
                )

        Follow(follower=bob, following=alice).save()
        Follow(follower=carol, following=alice).save()
        Follow(follower=peter, following=alice).save()

        followers = sorted(list(
            [x.url for x in alice.followers]))

        self.assertEqual(
                followers,
                [
                    'https://example.com/users/peter',
                    'https://testserver/users/bob',
                    'https://testserver/users/carol',
                    ],
                )

        mock_remote_object(
                url="https://example.com/users/peter/followers",
                content=REMOTE_FOLLOWERS_COLLECTION,
                )

        followers = sorted(list(
            [x.url for x in peter.followers]))

        self.assertEqual(
                followers,
                [
                    'https://example.com/users/quentin',
                    'https://example.com/users/roger',
                    'https://testserver/users/alice',
                    'https://testserver/users/bob',
                    ],
                )
