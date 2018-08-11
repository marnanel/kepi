from django.test import TestCase, Client
from django_kepi.views import User

class UserTests(TestCase):

    def test_collections(self):

        c = Client()
        activity = c.get('/collections/0').json()
        
        raise ValueError(str(activity))
