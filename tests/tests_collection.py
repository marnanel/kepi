from django.test import TestCase, Client
from django_kepi.models import Following
from django_kepi.views import FollowersView
import datetime

class CollectionTests(TestCase):

    def test_followers(self):

        c = Client(
                HTTP_ACCEPT = 'application/activity+json',
                )

        response = c.get('user/alice/followers')

        raise ValueError(str(response.content))
