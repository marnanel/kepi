# test_send.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from unittest import skip
from django.test import TestCase
from rest_framework.test import force_authenticate, APIClient
from django.conf import settings
from kepi.sombrero_sendpub.delivery import deliver
from kepi.trilby_api.models import RemotePerson
from kepi.trilby_api.tests import create_local_person
import httpretty

REMOTE_URL = 'https://remote.example.net/users/zachary'

class TestSend(TestCase):

    def _register_remote(self):
        httpretty.register_uri(
                # FIXME: not the user's address, just their (shared) inbox
                httpretty.POST,
                REMOTE_URL,
                '', # body is ignored
                )

        # FIXME Here we must also register an ActivityPub form of the user
        # at the remote end
        # FIXME It would be nice if we could check the Accept content-type

        self._zachary = RemotePerson(
                url = REMOTE_URL,
                username = 'zachary',
                )
        self._zachary.save()

        self._alice = create_local_person('alice')

        self._client = APIClient()
        self._client.force_authenticate(self._alice.local_user)

    @skip("TODO - mentions aren't yet implemented")
    @httpretty.activate
    def test_send_direct_message(self):

        result = self._client.post(
                path='/api/v1/statuses',
                format='json',
                data = {
                    'status': '@zachary@remote.example.net Hello world',
                    'visibility': 'direct',
                    },
                )

        self.assertEqual(result.status_code,
                200)

    @skip("TODO")
    def test_irrelevant(self):
        pass

    @skip("TODO - mentions aren't implemented")
    def test_mention(self):
        pass

    @httpretty.activate
    def test_follow(self):

        self._register_remote()
        result = self._client.post(
                path='/api/v1/accounts/%d/follow' % (
                    self._zachary.id,),
                format='json',
                )

        self.assertEqual(result.status_code,
                200)

    @skip("TODO")
    def test_accept_follow(self):
        pass

    @skip("TODO")
    def test_reject_follow(self):
        pass
