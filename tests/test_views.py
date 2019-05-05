import django_kepi.activity_model
from django.test import TestCase, Client
import logging

logger = logging.getLogger(name='django_kepi')

class TestActivityObjectView(TestCase):

    def test_activity_object_view(self):

        a = django_kepi.activity_model.Activity(
                f_actor = 'https://example.net/users/fred',
                f_object = 'https://example.net/articles/i-like-jam',
                f_type = 'L',
                identifier = 'https://example.com/obj/1234',
                )
        a.save()

        c = Client()
        result = c.get('/obj/1234')
        logger.info('Content: %s', result.content)
