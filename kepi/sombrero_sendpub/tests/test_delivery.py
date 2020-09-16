# test_delivery.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from unittest import skip
from django.test import TestCase
from kepi.sombrero_sendpub.delivery import deliver
from kepi.trilby_api.tests import create_local_person
from kepi.trilby_api.models import Follow
from unittest.mock import MagicMock
import kepi.bowler_pub.views as bowler_views
import json

TEST_ACTIVITY = {"hello": "world"}

class TestDelivery(TestCase):

    def setup_locals(self):
        self.alice = create_local_person("alice")
        self.bob = create_local_person("bob")
        self.carol = create_local_person("carol")

        self._real_inbox_view = bowler_views.InboxView.post
        self._local_mock = MagicMock(
                wraps=self._real_inbox_view,
                )
        bowler_views.InboxView.post = self._local_mock

    def test_send_to_local_users(self):

        self.setup_locals()

        deliver(
                activity = TEST_ACTIVITY,
                sender = self.alice,
                target_people = [
                    self.bob, self.carol,
                    ],
                )

        self._local_mock.assert_called_once()

    def test_send_to_local_users_not_self(self):

        self.setup_locals()

        deliver(
                activity = TEST_ACTIVITY,
                sender = self.alice,
                target_people = [
                    self.alice,
                    self.bob, self.carol,
                    ],
                )

        self._local_mock.assert_called_once()

    def test_send_to_followers_of_local_user(self):

        self.setup_locals()

        Follow(following=self.alice, follower=self.bob).save()
        Follow(following=self.alice, follower=self.carol).save()

        deliver(
                activity = TEST_ACTIVITY,
                sender = self.alice,
                target_followers_of = [
                    self.alice,
                    ],
                )

        self._local_mock.assert_called_once()

    @skip(reason="nyi")
    def test_send_to_remote_user(self):
        # FIXME
        pass

    @skip(reason="nyi")
    def test_send_to_followers_of_remote_user(self):
        # FIXME
        pass
