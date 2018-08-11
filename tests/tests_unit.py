from django.test import TestCase, Client
from django_kepi.views import ActivityObjectView
import json

class UserTests(TestCase):

    fixtures = ['kepi1',]

    def test_collections(self):

        c = Client()
        response = c.get('/obj/1')
        
        # we can't use .json() because it doesn't accept
        # "application/activity+json" as a JSON content-type
        activity = json.loads(str(response.content, encoding='UTF-8'))
        
        raise ValueError(str(activity))
