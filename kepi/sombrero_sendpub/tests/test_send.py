# test_send.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from unittest import skip
from django.test import TestCase
from rest_framework.test import force_authenticate, APIClient
from django.conf import settings
from kepi.sombrero_sendpub.delivery import deliver
from kepi.trilby_api.models import Person
from kepi.trilby_api.tests import create_local_person
import httpretty

REMOTE_URL = 'https://remote.example.net/users/zachary'

class TestSend(TestCase):

    def setUp(self):
        httpretty.register_uri(
                httpretty.POST,
                REMOTE_URL,
                '', # body is ignored
                )

        self._zachary = Person(
                remote_url = REMOTE_URL,
                remote_username = 'zachary',
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
