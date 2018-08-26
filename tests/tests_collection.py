from django.test import TestCase, Client
from django_kepi.models import Actor, Following
from django_kepi.views import FollowersView
import datetime
import json

EXAMPLE_SERVER = 'http://testserver'
JSON_TYPE = 'application/activity+json'

class CollectionTests(TestCase):

    def check_collection(self,
            path,
            expectedTotalItems):

        c = Client(
                HTTP_ACCEPT = JSON_TYPE,
                )

        response = c.get(path)
        self.assertEqual(response['Content-Type'], JSON_TYPE)

        result = json.loads(response.content.decode(encoding='UTF-8'))

        for field in [
                '@context',
                'id',
                'totalItems',
                'type',
                ]:
            self.assertIn(field, result)

        if expectedTotalItems==0:
            self.assertNotIn('first', result)
        else:
            self.assertIn('first', result)
            self.assertEqual(result['first'], EXAMPLE_SERVER+path+'?page=1')

        self.assertEqual(result['id'], EXAMPLE_SERVER+path)
        self.assertEqual(result['totalItems'], expectedTotalItems)
        self.assertEqual(result['type'], 'OrderedCollection')

    def check_collection_page(self,
            path,
            page_number,
            expectedTotalItems):

        c = Client(
                HTTP_ACCEPT = JSON_TYPE,
                )

        full_path = '{}?page={}'.format(path, page_number)

        response = c.get(full_path)
        self.assertEqual(response['Content-Type'], JSON_TYPE)

        result = json.loads(response.content.decode(encoding='UTF-8'))

        raise ValueError(str(result))

    def test_followers(self):

        alice = Actor(name='alice')
        alice.save()

        for i in range(100):

            if i!=0:
                a = Actor(
                        name='user%02d' % (i,),
                        )
                a.save()

                f = Following(
                        follower = a,
                        following = alice,
                        )
                f.save()

            self.check_collection(
                    path='/user/alice/followers/',
                    expectedTotalItems=i,
                    )

            if i!=0:
                self.check_collection_page(
                        path='/user/alice/followers/',
                        page_number=1,
                        expectedTotalItems=i,
                        )


