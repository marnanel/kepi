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
from kepi.bowler_pub.tests import create_local_person
import json

TEST_ACTIVITY = {"hello": "world"}

class TestDelivery(TestCase):

    def test_send_to_local_users(self):

        alice = create_local_person("alice")
        bob = create_local_person("bob")
        carol = create_local_person("carol")

        deliver(
                activity = TEST_ACTIVITY,
                sender = alice,
                target_people = [
                    bob, carol,
                    ],
                )

    def test_send_to_local_users_not_self(self):

        alice = create_local_person("alice")
        bob = create_local_person("bob")
        carol = create_local_person("carol")

        deliver(
                activity = TEST_ACTIVITY,
                sender = alice,
                target_people = [
                    alice,
                    bob, carol,
                    ],
                )

    @skip(reason="nyi")
    def test_send_to_followers_of_local_user(self):
        pass

    @skip(reason="nyi")
    def test_send_to_remote_user(self):
        pass

    @skip(reason="nyi")
    def test_send_to_followers_of_remote_user(self):
        pass
