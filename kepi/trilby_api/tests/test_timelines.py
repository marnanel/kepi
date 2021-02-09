# test_timelines.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from kepi.bowler_pub.tests import create_remote_person
from django.conf import settings
from unittest import skip
import httpretty

# Tests for timelines. API docs are here:
# https://docs.joinmastodon.org/methods/statuses/

class TestTimelines(TrilbyTestCase):

    def add_status(self, source, visibility, content):
        status = Status(
                account = source,
                content = content,
                visibility = visibility,
                )
        status.save()

        logger.info("Created status: %s", status)

        return status

    def timeline_contents(self,
            path,
            as_user = None,
            ):

        details = sorted([x['content'] \
                for x in self.get(
                path = path,
                as_user = as_user,
                )])

        result = ''
        for detail in details:

            if detail.startswith('<p>') and detail.endswith('</p>'):
                detail = detail[3:-4]

            result += detail

        logger.info("Timeline contents for %s as %s...",
                path,
                as_user)
        logger.info("   ...are %s",
                result)

        return result

    def test_public_as_anon(self):

        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='U')
        self.add_status(source=alice, content='C', visibility='X')
        self.add_status(source=alice, content='D', visibility='D')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                as_user = None,
                ),
            'A',
            )

    def test_public_as_user(self):

        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='U')
        self.add_status(source=alice, content='C', visibility='X')
        self.add_status(source=alice, content='D', visibility='D')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                as_user = alice,
                ),
            'A',
            )

    def test_public_as_follower(self):

        alice = create_local_person("alice")
        george = create_local_person("george")

        follow = Follow(
                follower = george,
                following = alice,
                offer = None,
                )
        follow.save()

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='U')
        self.add_status(source=alice, content='C', visibility='X')
        self.add_status(source=alice, content='D', visibility='D')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                as_user = george,
                ),
            'AC',
            )

    def test_public_as_stranger(self):

        alice = create_local_person("alice")
        henry = create_local_person("henry")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='U')
        self.add_status(source=alice, content='C', visibility='X')
        self.add_status(source=alice, content='D', visibility='D')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                as_user = henry,
                ),
            'A',
            )

    @httpretty.activate()
    def test_public_local_and_remote(self):

        alice = create_local_person("alice")
        peter = create_remote_person(
                remote_url = "https://example.com/users/peter",
                name = "peter",
                auto_fetch = True,
                )

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=peter, content='B', visibility='A')
        self.add_status(source=alice, content='C', visibility='A')
        self.add_status(source=peter, content='D', visibility='A')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                ),
            'ABCD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?local=true',
                ),
            'AC',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?local=false',
                ),
            'ABCD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?remote=true',
                ),
            'BD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?remote=false',
                ),
            'ABCD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?local=true&remote=true',
                ),
            '',
            )

    def test_public_only_media(self):

        # We don't support added media at present anyway,
        # so turning this on will always get the empty set

        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='A')
        self.add_status(source=alice, content='C', visibility='A')
        self.add_status(source=alice, content='D', visibility='A')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?only_media=true',
                ),
            '',
            )

    def test_public_max_since_and_min(self):

        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='A')
        status_c = self.add_status(source=alice, content='C', visibility='A')
        self.add_status(source=alice, content='D', visibility='A')

        c_id = str(status_c.id)

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?since='+c_id,
                ),
            'D',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?max_id='+c_id,
                ),
            'ABC',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public?min_id='+c_id,
                ),
            'CD',
            )

    def test_public_limit(self):

        alice = create_local_person("alice")

        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        for i in range(len(alphabet)):
            self.add_status(
                    source=alice,
                    content=alphabet[i],
                    visibility='A',
                    )

        for i in range(len(alphabet)):
            self.assertEqual(
                self.timeline_contents(
                    path = '/api/v1/timelines/public?limit='+str(i),
                    ),
                alphabet[:i],
                )

        # the default is specified as 20
        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                ),
            alphabet[:20],
            message = 'default is 20',
            )

    ###### home timeline

    def test_home_as_user(self):
        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='U')
        self.add_status(source=alice, content='C', visibility='X')
        self.add_status(source=alice, content='D', visibility='D')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                as_user = alice,
                ),
            'ABCD',
            )

    @skip("to be implemented later")
    def test_hashtag(self):
        raise NotImplementedError()

    @skip("to be implemented later")
    def test_account_statuses(self):
        # Special case: this isn't considered a timeline method
        # in the API, but it's similar enough that we test it here
        raise NotImplementedError()

    @skip("to be implemented later")
    def test_list(self):
        raise NotImplementedError()
