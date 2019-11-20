# test_deliver.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

# This file contains two classes to test delivery,
# for historical reasons.

from django.test import TestCase, Client
from django.conf import settings
from kepi.bowler_pub.delivery import deliver
from kepi.bowler_pub.create import create
from kepi.bowler_pub.models import AcObject
import kepi.bowler_pub.views as bowler_pub_views
from unittest.mock import Mock, patch
from . import *
import logging
import httpsig
import httpretty
import json
import requests

# FIXME test caching
# FIXME test invalid keys

logger = logging.getLogger(name='kepi')

REMOTE_PATH_NAMES = {
        '/users/fred/inbox': 'fred',
        '/users/jim/inbox': 'jim',
        }

class TestDelivery(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def _set_up_remote_user_mocks(self):

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0001.json', 'r'))

        create_remote_person(
                url = REMOTE_FRED,
                name = 'fred',
                publicKey = keys['public'],
                inbox = FREDS_INBOX,
                followers = FREDS_FOLLOWERS,
                )

        create_remote_collection(
                url = FREDS_FOLLOWERS,
                items=[
                    REMOTE_JIM,
                    LOCAL_ALICE,
                    LOCAL_BOB,
                    JIMS_FOLLOWERS, # which we should ignore
                    ],
                )

        create_remote_person(
                url = REMOTE_JIM,
                name = 'jim',
                publicKey = keys['public'],
                inbox = JIMS_INBOX,
                followers = JIMS_FOLLOWERS,
                )

        create_remote_collection(
                url = JIMS_FOLLOWERS,
                items=[
                    LOCAL_BOB,
                    ],
                )

    def _set_up_remote_request_mocks(self):
        mock_remote_object(
                FREDS_INBOX,
                as_post = True,
                )

        mock_remote_object(
                JIMS_INBOX,
                as_post = True,
                )

    def _set_up_local_user_mocks(self):

        keys = json.load(open('kepi/bowler_pub/tests/keys/keys-0002.json', 'r'))

        # I know these aren't mocks. This is just for consistency.
        create_local_person(name='alice',
                privateKey = keys['private'])
        create_local_person(name='bob')

    @patch.object(bowler_pub_views.activitypub.ActorView, 'activity_store')
    @httpretty.activate
    def _test_delivery(self,
            fake_local_request,
            to,
            expected,
            ):
        """
        Delivers a Like, and makes assertions about what happened.
        Also, creates all the background stuff needed to do so.

        "to" is a list of ActivityPub IDs which we'll put in
            the "to" field of the Like.
        "expected" is a list of strings asserting which inboxes
            get touched. Remote inboxes are represented by
            the name of the user (like "jim"); local inboxes
            are represented by the URL path, minus the
            leading slash.
        """

        self._set_up_remote_user_mocks()
        self._set_up_remote_request_mocks()
        self._set_up_local_user_mocks()

        like = create(
                value = {
                    'type': 'Like',
                    'actor': LOCAL_ALICE,
                    'object': REMOTE_FRED,
                    'to': to,
                    },
                )
        like.save()

        #################
        # Assertions

        touched = []
        for req in httpretty.httpretty.latest_requests:
            if req.method=='POST':
                touched.append(
                        REMOTE_PATH_NAMES.get(req.path, req.path),
                        )

        for obj, kwargs in fake_local_request.call_args_list:
            touched.append(kwargs['username'])

        logger.info('Inboxes touched:  %s', sorted(touched))
        logger.info('Inboxes expected: %s', sorted(expected))

        self.assertListEqual(
                sorted(touched),
                sorted(expected),
                )

    def test_simple_remote_and_local(self):
        self._test_delivery(
                to=[REMOTE_FRED, LOCAL_BOB],
                expected=['alice', 'fred', 'bob'],
                )

    def test_simple_local(self):
        self._test_delivery(
                to=[LOCAL_BOB],
                expected=['alice', 'bob'],
                )

    def test_simple_remote(self):
        self._test_delivery(
                to=[REMOTE_FRED],
                expected=['alice', 'fred'],
                )

    def test_not_to_self(self):
        self._test_delivery(
                to=[LOCAL_ALICE],
                expected=['alice'],
                )

    def test_not_to_public_url(self):
        self._test_delivery(
                to=[PUBLIC],
                expected=['alice'],
                )

    def test_not_to_public_as(self):
        self._test_delivery(
                to=['as:Public'],
                expected=['alice'],
                )

    def test_not_to_public_bare(self):
        self._test_delivery(
                to=['Public'],
                expected=['alice'],
                )

    def test_remote_followers(self):
        self._test_delivery(
                to=[REMOTE_FRED, FREDS_FOLLOWERS],
                expected=['fred', 'jim', 'alice', 'bob'],
                )
