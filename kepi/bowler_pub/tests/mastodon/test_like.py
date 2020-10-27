# test_person.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import httpretty
from django.test import TestCase
from kepi.trilby_api.tests import create_local_status, create_local_person
from kepi.bowler_pub.create import create

import logging
logger = logging.getLogger(name='kepi')

class Tests(TestCase):

    @httpretty.activate
    def test_like(self):

        sender = create_local_person('sender')
        recipient = create_local_person('recipient')
        status = create_local_status(posted_by=sender)

        self.assertFalse(
                sender.has_liked(status),
                )

        object_json = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'id': 'foo',
            'type': 'Like',
            'actor': sender.url,
            'object': status.url,
          }

        like = create(
                fields=object_json,
                )

        self.assertTrue(
                sender.has_liked(status),
                msg = 'creates a favourite from sender to status',
                )
