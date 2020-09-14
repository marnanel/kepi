# test_person.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from kepi.trilby_api.tests import *
from unittest import skip
from rest_framework.test import APIClient, force_authenticate
import logging

logger = logging.getLogger(name='kepi')

# This needs expanding into a full unit test.

class TestPerson(TrilbyTestCase):

    def test_followers(self):

        alice = create_local_person(name='alice')
        bob = create_local_person(name='bob')
        carol = create_local_person(name='carol')

        Follow(follower=bob, following=alice).save()
        Follow(follower=carol, following=alice).save()

        followers = sorted(list(
            [x.url for x in alice.followers]))

        self.assertEqual(
                followers,
                ['https://testserver/users/bob', 'https://testserver/users/carol']
        )

        # FIXME test the "followers" property on a RemotePerson
