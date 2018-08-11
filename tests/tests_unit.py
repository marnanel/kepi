from django.test import TestCase, Client
from django_kepi.views import ActivityObjectView

class UserTests(TestCase):

    def test_collections(self):

        c = Client()
        activity = c.get('/obj/0').json()
        
        raise ValueError(str(activity))
