from django.test import TestCase
from kepi.bowler_pub.tests import create_remote_person
from unittest import skip
from kepi.bowler_pub.create import create
from kepi.bowler_pub.models import *
import httpretty
import logging

logger = logging.getLogger(name='kepi')

SENDER_ID = 'https://example.com/actor'
TOTALLY = "Totally modified now"

# XXX Why does this only test updating of profiles?
# XXX I thought we should update items as well.

class TestUpdate(TestCase):

    @httpretty.activate
    def test_update_profile(self):

        sender = create_remote_person(
                name = 'jeremy',
                remote_url = SENDER_ID,
                auto_fetch = True,
                )

        create_form = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'id': 'foo',
                'type': 'Update',
                'actor': SENDER_ID,
                'object': {
                    'display_name': TOTALLY,
                    },
                }

        logger.info('Submitting Update activity: %s', create_form)
        create(create_form)

        self.assertEqual(
                sender.display_name,
                TOTALLY,
                msg = "it updates profile",
                )
