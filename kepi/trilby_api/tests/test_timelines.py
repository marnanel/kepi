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

class TimelineTestCase(TrilbyTestCase):

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
            data = None,
            as_user = None,
            ):

        details = sorted([x['content'] \
                for x in self.get(
                path = path,
                data = data,
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

class TestPublicTimeline(TimelineTestCase):

    def test_as_anon(self):

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

    def test_as_user(self):

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

    def test_as_follower(self):

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

    def test_as_stranger(self):

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
    def test_local_and_remote(self):

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
                path = '/api/v1/timelines/public',
                data = {'local': True},
                ),
            'AC',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'local': False},
                ),
            'ABCD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'remote': True},
                ),
            'BD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'remote': False},
                ),
            'ABCD',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'local': True, 'remote': True},
                ),
            '',
            )

    def test_only_media(self):

        # We don't support added media at present anyway,
        # so turning this on will always get the empty set

        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='A')
        self.add_status(source=alice, content='C', visibility='A')
        self.add_status(source=alice, content='D', visibility='A')

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'only_media': True},
                ),
            '',
            )

    def test_max_since_and_min(self):

        alice = create_local_person("alice")

        self.add_status(source=alice, content='A', visibility='A')
        self.add_status(source=alice, content='B', visibility='A')
        status_c = self.add_status(source=alice, content='C', visibility='A')
        self.add_status(source=alice, content='D', visibility='A')

        c_id = str(status_c.id)

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'since': status_c.id},
                ),
            'D',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'max_id': status_c.id},
                ),
            'ABC',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                data = {'min_id': status_c.id},
                ),
            'CD',
            )

    def test_limit(self):

        alice = create_local_person("alice")

        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        for i in range(len(alphabet)):
            self.add_status(
                    source=alice,
                    content=alphabet[i],
                    visibility='A',
                    )

        for i in range(1, len(alphabet)):
            self.assertEqual(
                self.timeline_contents(
                    path = '/api/v1/timelines/public',
                    data = {'limit': i},
                    ),
                alphabet[:i],
                )

        # the default is specified as 20
        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/public',
                ),
            alphabet[:20],
            msg = 'default is 20',
            )

class TestHomeTimeline(TimelineTestCase):

    def add_standard_statuses(self):
        self.alice = create_local_person("alice")
        self.bob = create_local_person("bob")
        self.carol = create_local_person("carol")

        self.add_status(source=self.bob, content='A', visibility='A')
        self.add_status(source=self.carol, content='B', visibility='A')
        self.add_status(source=self.carol, content='C', visibility='A')
        self.add_status(source=self.bob, content='D', visibility='A')

        Follow(
                follower=self.alice,
                following=self.bob,
                offer=None).save()

    def follow_carol(self):
        Follow(
                follower=self.alice,
                following=self.carol,
                offer=None).save()

    def test_not_anon(self):
        found = self.get(
                path = '/api/v1/timelines/home',
                as_user = None,
                expect_result = 401,
                )

    def test_0_simple(self):

        self.add_standard_statuses()

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                as_user = self.alice,
                ),
            'AD',
            )

        self.follow_carol()

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                as_user = self.alice,
                ),
            'ABCD',
            )

    def test_max_since_and_min(self):

        self.add_standard_statuses()

        c_id = '3' # FIXME hack

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                data = {'since': c_id},
                as_user = self.alice,
                ),
            'D',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                data = {'max_id': c_id},
                as_user = self.alice,
                ),
            'A',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                data = {'min_id': c_id},
                as_user = self.alice,
                ),
            'D',
            )

        self.follow_carol()

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                data = {'since': c_id},
                as_user = self.alice,
                ),
            'D',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                data = {'max_id': c_id},
                as_user = self.alice,
                ),
            'ABC',
            )

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                data = {'min_id': c_id},
                as_user = self.alice,
                ),
            'CD',
            )

    def test_limit(self):

        self.alice = create_local_person("alice")
        self.bob = create_local_person("bob")
        self.carol = create_local_person("carol")

        Follow(
                follower=self.alice,
                following=self.bob,
                offer=None).save()

        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        for i in range(len(alphabet)):
            self.add_status(
                    source=self.bob,
                    content=alphabet[i],
                    visibility='A',
                    )

            self.add_status(
                    source=self.carol,
                    content=alphabet[i].lower(),
                    visibility='A',
                    )

        for i in range(1, len(alphabet)):
            self.assertEqual(
                self.timeline_contents(
                    path = '/api/v1/timelines/home',
                    data = {'limit': i},
                    as_user = self.alice,
                    ),
                alphabet[:i],
                )

        # the default is specified as 20
        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                as_user = self.alice,
                ),
            alphabet[:20],
            msg = 'default is 20',
            )

    @httpretty.activate()
    def test_local(self):

        self.add_standard_statuses()

        self.peter = create_remote_person(
                remote_url = "https://example.com/users/peter",
                name = "peter",
                auto_fetch = True,
                )
        self.add_status(source=self.peter, content='P', visibility='A')
        self.add_status(source=self.peter, content='Q', visibility='A')
        Follow(
                follower = self.alice,
                following = self.peter,
                offer = None,
                ).save()

        self.assertEqual(
            self.timeline_contents(
                path = '/api/v1/timelines/home',
                as_user = self.alice,
                ),
            'ABCDPQ',
            )

        self.assertEqual(
                self.timeline_contents(
                    path = '/api/v1/timelines/home',
                    data = {'local': True},
                    as_user = self.alice,
                    ),
                'ABCD',
                )

class TestTimelinesNotImplemented(TimelineTestCase):
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
