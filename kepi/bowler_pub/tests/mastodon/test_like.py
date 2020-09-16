from kepi.trilby_api.tests import create_local_status, create_local_person
from unittest import skip
from kepi.bowler_pub.create import create
from django.test import TestCase

class TestLike(TestCase):

    @skip("this assumes we can ask Person.has_favourited(); we can't yet")
    def test_like(self):

        sender = create_local_person('sender')
        recipient = create_local_person('recipient')
        status = create_local_status(posted_by=sender.id)

        object_json = {
            '@context': 'https://www.w3.org/ns/activitystreams',
            'id': 'foo',
            'type': 'Like',
            'actor': sender.id,
            'object': status.id,
          }

        status = create(**object_json)

        self.assertTrue(
                sender.has_favourited(status),
                msg = 'creates a favourite from sender to status',
                )
