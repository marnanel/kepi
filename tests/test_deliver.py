# test_deliver.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

# This file contains two classes to test delivery,
# for historical reasons.

from django.test import TestCase, Client
from django_kepi.delivery import deliver
from django_kepi.create import create
from django_kepi.models import Object
import django_kepi.views
from unittest.mock import Mock, patch
from . import *
import logging
import httpsig
import httpretty
import json
import requests

# FIXME test caching
# FIXME test invalid keys

logger = logging.getLogger(name='django_kepi')

REMOTE_PATH_NAMES = {
        '/users/fred/inbox': 'fred',
        '/users/jim/inbox': 'jim',
        }

def _message_became_activity(url=ACTIVITY_ID):
    try:
        result = Object.objects.get(remote_url=url)
        return True
    except Object.DoesNotExist:
        return False

class TestDeliverTasks(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def _run_delivery(
            self,
            activity_fields,
            remote_user_details,
            remote_user_endpoints,
            ):

        a = create(value=activity_fields)
        a.save()

        for who, what in remote_user_details.items():
            mock_remote_object(
                    url = who,
                    content = json.dumps(what),
                    )

        for who in remote_user_endpoints:
            mock_remote_object(
                    url = who,
                    content = 'Thank you',
                    as_post = True,
                    )

        deliver(a.number)

    @httpretty.activate
    def test_deliver_remote(self):

        keys = json.load(open('tests/keys/keys-0000.json', 'r'))

        alice = create_local_person(
                name = 'alice',
                publicKey = keys['public'],
                privateKey = keys['private'],
                )

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': REMOTE_FRED,
                    'to': [REMOTE_FRED],
                    },
                remote_user_details = {
                    REMOTE_FRED: remote_user(
                        url=REMOTE_FRED,
                        name='Fred',
                        sharedInbox=REMOTE_SHARED_INBOX,
                        ),
                    },
                remote_user_endpoints = [
                    REMOTE_SHARED_INBOX,
                    ],
                )

    @httpretty.activate
    def test_deliver_local(self):

        keys0 = json.load(open('tests/keys/keys-0000.json', 'r'))
        keys1 = json.load(open('tests/keys/keys-0001.json', 'r'))
        alice = create_local_person(
                name = 'alice',
                publicKey = keys0['public'],
                privateKey = keys0['private'],
                )
        bob = create_local_person(
                name = 'bob',
                publicKey = keys1['public'],
                privateKey = keys1['private'],
                )

        self._run_delivery(
                activity_fields = {
                    'type': 'Follow',
                    'actor': LOCAL_ALICE,
                    'object': LOCAL_BOB,
                    'to': [LOCAL_BOB],
                    },
                remote_user_details = {
                    },
                remote_user_endpoints = [
                    ],
                )

        # FIXME add some assertions!

class TestDelivery(TestCase):

    def _set_up_remote_user_mocks(self):

        keys = json.load(open('tests/keys/keys-0001.json', 'r'))

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

        keys = json.load(open('tests/keys/keys-0002.json', 'r'))

        # I know these aren't mocks. This is just for consistency.
        create_local_person(name='alice',
                privateKey = keys['private'])
        create_local_person(name='bob')

    @patch.object(django_kepi.views.activitypub.InboxView, 'activity_store')
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

        deliver(like.number)

        #################
        # Assertions

        touched = []
        for req in httpretty.httpretty.latest_requests:
            if req.method=='POST':
                touched.append(
                        REMOTE_PATH_NAMES.get(req.path, req.path),
                        )

        if fake_local_request.call_args:
            for req in fake_local_request.call_args:
                try:
                    path = req[0].path
                    touched.append(path)
                except KeyError:
                    pass

        logger.info('Inboxes touched: %s', touched)
        logger.info('  " "  expected: %s', expected)

        self.assertListEqual(
                sorted(touched),
                sorted(expected),
                )

    def test_simple_remote_and_local(self):
        self._test_delivery(
                to=[REMOTE_FRED, LOCAL_BOB],
                expected=['fred', '/sharedInbox'],
                )

    def test_simple_local(self):
        self._test_delivery(
                to=[LOCAL_BOB],
                expected=['/sharedInbox'],
                )

    def test_simple_remote(self):
        self._test_delivery(
                to=[REMOTE_FRED],
                expected=['fred'],
                )

    def test_not_to_self(self):
        self._test_delivery(
                to=[LOCAL_ALICE],
                expected=[],
                )

    def test_not_to_public_url(self):
        self._test_delivery(
                to=[PUBLIC],
                expected=[],
                )

    def test_not_to_public_as(self):
        self._test_delivery(
                to=['as:Public'],
                expected=[],
                )

    def test_not_to_public_bare(self):
        self._test_delivery(
                to=['Public'],
                expected=[],
                )

    def test_remote_followers(self):
        self._test_delivery(
                to=[REMOTE_FRED, FREDS_FOLLOWERS],
                expected=['fred', 'jim', '/sharedInbox'],
                )
