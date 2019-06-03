from django.test import TestCase, Client
from unittest import skip
from django_kepi.models import *
import datetime
import json
from django_kepi import logger
from django_kepi.find import find
from . import *

EXAMPLE_SERVER = 'http://testserver'
JSON_TYPE = 'application/activity+json'
PAGE_LENGTH = 50

class CollectionTests(TestCase):

    def check_collection(self,
            path,
            expectedTotalItems):

        c = Client(
                HTTP_ACCEPT = JSON_TYPE,
                )

        response = c.get(path)

        if response.status_code!=200:
            raise RuntimeError(response.content)

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
            expectedTotalItems,
            expectedOnPage,
            ):

        def full_path(page):
            if page is None:
                query = ''
            else:
                query = '?page={}'.format(page)

            return EXAMPLE_SERVER + path + query

        c = Client(
                HTTP_ACCEPT = JSON_TYPE,
                )

        response = c.get(full_path(page_number))

        if response['Content-Type']=='text/html':
            # let's just give up here so they have a chance
            # of figuring out the error message from the server.
            raise RuntimeError(response.content)

        self.assertEqual(response['Content-Type'], JSON_TYPE)

        result = json.loads(response.content.decode(encoding='UTF-8'))

        for field in [
                '@context',
                'id',
                'totalItems',
                'type',
                'partOf',
                ]:
            self.assertIn(field, result)

        self.assertEqual(result['id'], full_path(page_number))
        self.assertEqual(result['totalItems'], expectedTotalItems)
        self.assertEqual(result['type'], 'OrderedCollectionPage')
        self.assertEqual(result['orderedItems'], expectedOnPage)
        self.assertEqual(result['partOf'], full_path(None))

        if page_number!=1:
            self.assertIn('prev', result)
            self.assertEqual(result['prev'], full_path(page_number-1))
        else:
            self.assertNotIn('prev', result)

        if (page_number-1)<int((expectedTotalItems-1)/PAGE_LENGTH):
            self.assertIn('next', result)
            self.assertEqual(result['next'], full_path(page_number+1))
        else:
            self.assertNotIn('next', result)

    def test_usageByOtherApps(self):

        PATH = '/users'
        EXPECTED_SERIALIZATION = [
                {'id': 'https://altair.example.com/users/alice', 'name': 'alice', 'type': 'Person', },
                {'id': 'https://altair.example.com/users/bob', 'name': 'bob', 'type': 'Person', },
                {'id': 'https://altair.example.com/users/carol', 'name': 'carol', 'type': 'Person', },
                ]

        users = [
                create_local_person(name='alice'),
                create_local_person(name='bob'),
                create_local_person(name='carol'),
                ]

        for user in users:
            user.save()

        self.check_collection(
                path=PATH,
                expectedTotalItems=len(users),
                )

        self.check_collection_page(
                path=PATH,
                page_number=1,
                expectedTotalItems=len(users),
                expectedOnPage=EXPECTED_SERIALIZATION,
                )

    def test_followers_and_following(self):

        self.maxDiff = None

        people = {}

        for name in ['alice', 'bob', 'carol']:
            people[name] = create_local_person(name = name)

            follow = create(
                    f_type = 'Follow',
                    actor = people[name],
                    f_object = people['alice'],
                )

            create(
                    f_type = 'Accept',
                    actor = people['alice'],
                    f_object = follow,
                )

        path = '/users/alice/followers'

        self.check_collection(
                path=path,
                expectedTotalItems=3,
                )

        self.check_collection_page(
                path=path,
                page_number=1,
                expectedTotalItems=3,
                expectedOnPage=[
                    'https://altair.example.com/users/alice',
                    'https://altair.example.com/users/bob',
                    'https://altair.example.com/users/carol',
                    ],
                )

        for name in ['alice', 'bob', 'carol']:

            path='/users/{}/following'.format(name)

            self.check_collection(
                    path=path,
                    expectedTotalItems=1,
                    )

            self.check_collection_page(
                    path=path,
                    page_number=1,
                    expectedTotalItems=1,
                    expectedOnPage=[
                        'https://altair.example.com/users/alice',
                    ],
                     )


