from django.test import TestCase, Client
from django_kepi.views import ActivityObjectView
from django_kepi.models import ActivityObject
import json

class UserTests(TestCase):

    fixtures = ['kepi1',]

    def _get_json(self, url):
        c = Client()
        response = c.get(url)

        self.assertEqual(response['Content-Type'],
                'application/activity+json',
                )
        
        # we can't use .json() because it doesn't accept
        # "application/activity+json" as a JSON content-type
        # https://code.djangoproject.com/ticket/29662
        return json.loads(str(response.content, encoding='UTF-8'))

    def test_basic_objects(self):

        activity = self._get_json('/obj/1')
        self.assertEqual(activity['id'], 1)
        self.assertEqual(activity['type'], 'Object')

        activity = self._get_json('/obj/2')
        self.assertEqual(activity['id'], 2)
        self.assertEqual(activity['type'], 'Object')

    def test_does_not_exist(self):

        with self.assertRaises(ActivityObject.DoesNotExist):
            self._get_json('/obj/0')
