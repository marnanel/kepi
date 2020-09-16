# test_headers.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name="kepi")

from django.test import TestCase, Client
from kepi.trilby_api.tests import create_local_person
from django.conf import settings
from unittest import skip

MIME_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'

@skip("The header middleware is causing problems with testing at present")
class TestHeaders(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'
        self.alice = create_local_person('alice')
        self.client = Client()
        self.alice_url = settings.KEPI['USER_URL_FORMAT'] % {
                'username': 'alice',
                'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                }

    def test_link(self):

        response = self.client.get(self.alice_url,
                HTTP_ACCEPT = MIME_TYPE,
                )

        links = response['Link'].split(', ')

        self.assertEqual(
                links,
                [
                    '<https://testserver/.well-known/webfinger?resource='+\
                    'acct%3Aalice%40testserver>; rel="lrdd"; '+\
                    'type="application/xrd+xml"',

                    '<https://testserver/users/alice/feed>; '+\
                    'rel="alternate"; type="application/atom+xml"',

                    '<https://testserver/users/alice>; '+\
                    'rel="alternate"; type="application/activity+json"',
                    ])

    def test_standard_headers(self):

        response = self.client.get(self.alice_url,
                HTTP_ACCEPT = MIME_TYPE,
                )

        for field, value in [
                ('X-Content-Type-Options', 'nosniff'),
                ('X-XSS-Protection', '1; mode=block'),
                ('Vary', 'Accept, Accept-Encoding, Origin'),
                ('Cache-Control', 'max-age=180, public'),
                ('Transfer-Encoding', 'chunked'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload'),
                ('Referrer-Policy', 'no-referrer-when-downgrade'),
                ('X-Frame-Options', 'DENY'),
                ]:

            self.assertEqual(
                    response[field],
                    value,
                    )
