from django.test import TestCase
from tests import create_local_note, create_local_person
from unittest import skip
from django_kepi.create import create
from django_kepi.models import *
import logging

SENDER_ID = 'https://example.com/actor'
SENDER_DOMAIN = 'example.com'
SENDER_FOLLOWERS = 'https://example.com/followers'

logger = logging.getLogger(name='tests')

# XXX Why does this only test updating of profiles?
# XXX I thought we should update items as well.

class TestUpdate(TestCase):

    @skip("hardly written")
    def test_update_profile(self):

        sender = create_local_person()

        object_json = {
                '@context': 'https://www.w3.org/ns/activitystreams',
                'id': 'foo',
                'type': 'Update',
                'actor': sender,
                'object': actor_json,
                }
        self.assertEqual(
                sender.display_name,
                "Totally modified now",
                )
