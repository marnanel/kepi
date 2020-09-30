# test_timelines.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for timelines. API docs are here:
# https://docs.joinmastodon.org/methods/statuses/

TIMELINE_DATA = [
        # Visibility is:
        #   A=public: visible to anyone, and in public timelines
        #   U=unlisted: visible to anyone, but not in public timelines
        #   X=private: visible to followers and anyone tagged
        #   D=direct: visible only to those who are tagged

        # We haven't yet implemented:
        #   - (user) tags
        #   - hashtags
        #   - user lists
        #   - following users but hiding reblogs
        # and when we do, these tests will need updating.
        #
        # All statuses are posted by alice.
        #
        # id   visibility  visible in
        ( 'A', 'A',
            ['public', 'follower', 'stranger', 'home', ], ),
        ( 'B', 'U',
            ['follower', 'stranger', 'home', ], ),
        ( 'C', 'X',
            ['follower', 'home',], ),
        ( 'D', 'D',
            ['home', ], ),

        ]

class TestTimelines(TrilbyTestCase):

    def _set_up(self):

        self._alice = create_local_person("alice")

        for (id, visibility, visible_in) in TIMELINE_DATA:
            status = Status(
                    account = self._alice,
                    content = id,
                    visibility = visibility,
                    )
            status.save()

    def _check_timelines(self,
            situation,
            path,
            as_user):

        expected = []
        for (id, visibility, visible_in) in TIMELINE_DATA:
            if situation in visible_in:
                expected.append(f'<p>{id}</p>')
        expected = sorted(expected)

        details = sorted([x['content'] \
                for x in self.get(
                path = path,
                as_user = as_user,
                )])

        self.assertListEqual(
                expected,
                details,
                msg = f"Visibility in '{situation}' mismatch: "+\
                        f"expected {expected}, but got {details}.",
                        )

    def test_public(self):
        self._set_up()

        self._check_timelines(
            situation = 'public',
            path = '/api/v1/timelines/public',
            as_user = None,
            )

    def test_follower(self):
        self._set_up()
        self._george = create_local_person("george")

        follow = Follow(
                follower = self._george,
                following = self._alice,
                offer = None,
                )
        follow.save()

        self._check_timelines(
            situation = 'public',
            path = '/api/v1/timelines/public',
            as_user = self._george,
            )

    def test_stranger(self):
        self._set_up()
        self._henry = create_local_person("henry")

        self._check_timelines(
            situation = 'public',
            path = '/api/v1/timelines/public',
            as_user = self._henry,
            )

    def test_home(self):
        self._set_up()

        self._check_timelines(
            situation = 'home',
            path = '/api/v1/timelines/home',
            as_user = self._alice,
            )

    @skip("Hashtags not yet implemented")
    def test_hashtag(self):
        pass

    @skip("Not yet implemented")
    def test_account_statuses(self):
        # Special case: this isn't considered a timeline method
        # in the API, but it's similar enough that we test it here
        pass

    @skip("Lists not yet implemented")
    def test_list(self):
        pass
