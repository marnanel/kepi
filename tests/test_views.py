from django_kepi.activity_model import Activity
from django.test import TestCase, Client
from things_for_testing.models import ThingUser
import logging
import json

logger = logging.getLogger(name='django_kepi')

class TestSingleKepiView(TestCase):

    def test_single_kepi_view(self):

        alice = ThingUser(
                name = 'alice',
                favourite_colour = 'magenta',
                )
        alice.save()

        c = Client()
        response = c.get('/users/alice')
        logger.info('Response: %s', response.content.decode('utf-8'))
        result = json.loads(response.content.decode('utf-8'))

        self.assertDictEqual(
                result,
                {
                    'name': 'alice',
                    'favourite_colour': 'magenta',
                    'id': 'https://altair.example.com/users/alice',
                    },
                )
