# test_with_sombrero.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

import django.test
import httpretty
from kepi.trilby_api.models import Follow
from kepi.trilby_api.tests import create_local_person, create_local_status
from kepi.bowler_pub.tests import create_remote_person, mock_remote_object

class Tests(django.test.TestCase):

    @httpretty.activate
    def test_with_sombrero(self):

        """
        Tests whether creating a local status causes a
        message to be sent to remote followers of the creator.

        This is a regression test for issue 42:
        https://gitlab.com/marnanel/kepi/-/issues/42
        """

        self.alice = create_local_person("alice")

        self.bob = create_remote_person(
                url = 'https://example.org/people/bob',
                name = 'bob',
                auto_fetch = True,
                )
        self.seen_message = False

        def seen():
            logger.info("Message received.")
            self.seen_message = True

        mock_remote_object(
                url = 'https://example.org/people/bob/inbox',
                content = 'Thank you',
                status = 200,
                as_post = True,
                on_fetch = seen,
                )

        Follow(following=self.alice, follower=self.bob).save()

        create_local_status(
                posted_by = self.alice,
                content = "I'll tell you the tale of the sweet nightingale.",
                )

        self.assertTrue(self.seen_message,
                msg="The remote server received the message.")
