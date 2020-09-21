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
from kepi.bowler_pub.tests import create_remote_person, mock_remote_object
import kepi.bowler_pub.views as bowler_views
import httpretty

TEST_ACTIVITY = {
        'id': 'https://example.com/foo',
        'type': 'Create',
        'actor': 'alice@example.com',
        'object': {
            'type': 'Note',
            'content': 'Lorem ipsum',
          },
        }

class Tests(TestCase):

    def setup_locals(self):
        self.alice = create_local_person("alice")
        self.bob = create_local_person("bob")
        self.carol = create_local_person("carol")

        self._real_inbox_post = bowler_views.InboxView.post
        self.remotes = {}
        self.received_post = set()

        def mock_post(*args, **kwargs):
            """
            Wrapper for InboxView.post(), which flags that
            the local view has received a copy of the message.

            Adds the name of the user to self.received_post.
            If the message was sent to the local shared inbox,
            adds "(shared)".
            """
            logger.info("Received local post")

            self.received_post.add(
                    kwargs.get("username") or "(shared)")

            logger.info("%s %s %s",
                    self.received_post,
                    kwargs,
                    kwargs.get("username", "(shared"))

            result = self._real_inbox_post(*args, **kwargs)
            return result

        bowler_views.InboxView.post = mock_post

    def acknowledge_remote(self, name):
        logger.info("Received remote post for %s", name)
        self.received_post.add(name)

    def setup_remotes(self):

        for name in ['peter', 'robert', 'quentin']:
            self.remotes[name] = create_remote_person(
                    url = 'https://example.org/people/'+name,
                    name = name,
                    auto_fetch = True,
                    )

            # and the inbox:
            mock_remote_object(
                    url = f'https://example.org/people/{name}/inbox',
                    content = 'Thank you',
                    status = 200,
                    as_post = True,
                    on_fetch = lambda n=name: self.acknowledge_remote(n),
                    )

    def test_send_to_local_users(self):

        self.setup_locals()

        deliver(
                activity = TEST_ACTIVITY,
                sender = self.alice,
                target_people = [
                    self.bob, self.carol,
                    ],
                )

        self.assertEqual(
                self.received_post,
                set(['(shared)']),
                )

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

        self.assertEqual(
                self.received_post,
                set(['(shared)']),
                )

    @httpretty.activate
    def test_send_to_remote_user(self):
        self.setup_locals()
        self.setup_remotes()

        deliver(
                activity = TEST_ACTIVITY,
                sender = self.alice,
                target_people = [
                    self.remotes['peter'],
                    ],
                )

        self.assertEqual(
                self.received_post,
                set(['peter']),
                )

    @httpretty.activate
    def test_send_to_followers_of_remote_user(self):
        self.setup_locals()
        self.setup_remotes()

        mock_remote_object(
                url = 'https://example.org/people/peter/followers',
                content = """{
                "id":"https://example.org/people/peter/followers",
                "type":"OrderedCollection",
                "totalItems":2,
                "orderedItems":[
                "https://example.org/people/quentin",
                "https://example.org/people/robert"
                ]
                }""",
                status = 200,
                )

        deliver(
                activity = TEST_ACTIVITY,
                sender = self.alice,
                target_followers_of = [
                    self.remotes['peter'],
                    ],
                )

        self.assertEqual(
                self.received_post,
                set(['quentin', 'robert']),
                )
