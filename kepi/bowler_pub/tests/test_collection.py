from django.test import TestCase, Client
from unittest import skip
from kepi.bowler_pub.models import *
import datetime
import json
from kepi.bowler_pub.find import find
from kepi.bowler_pub.utils import as_json
from . import *
import logging

logger = logging.Logger('kepi')

EXAMPLE_SERVER = 'http://testserver'
JSON_TYPE = 'application/activity+json; charset=utf-8'
PAGE_LENGTH = 50

class CollectionTests(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'
        self.maxDiff = None

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

            self.assertIn('last', result)

            lastpage = 1 + int((expectedTotalItems+1)/PAGE_LENGTH)

            self.assertEqual(result['last'], EXAMPLE_SERVER+path+\
                    ('?page=%d' % (lastpage,)))

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
        self.assertEqual(result['partOf'], full_path(None))
        self.assertEqual(len(expectedOnPage), len(result['orderedItems']))

        for actual, expected in zip(result['orderedItems'], expectedOnPage):
            if type(expected)==dict:
                self.assertDictContainsSubset(expected, actual)
            else:
                self.assertEqual(expected, actual)

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

    @skip("this is really slow")
    def test_lots_of_entries(self):
        alice = create_local_person(name='alice')

        PATH = '/users/alice/outbox'
        NUMBER_OF_PASSES = 100
        statuses = []

        for i in range(0, 103):

            logger.info(' =================== test_lots_of_entries, pass %d / %d',
                i, NUMBER_OF_PASSES)

            logger.info(' == Index?')
            self.check_collection(
                    path=PATH,
                    expectedTotalItems=len(statuses),
                    )

            lastpage = int((len(statuses))/PAGE_LENGTH)

            # nb that "page" here is 0-based, but
            # ActivityPub sees it as 1-based

            for page in range(lastpage+1):

                logger.info(' == Page %d/%d?', page, lastpage)

                if page==lastpage:
                    expecting = statuses[page*PAGE_LENGTH:]
                else:
                    expecting = statuses[page*PAGE_LENGTH:((page+1)*PAGE_LENGTH)]

                expecting = [json.loads(x) for x in expecting]

                self.check_collection_page(
                        path=PATH,
                        page_number=page+1,
                        expectedTotalItems=len(statuses),
                        expectedOnPage=expecting,
                        )

            statuses.append(as_json(create_local_note(
                    attributedTo = alice,
                    content = 'Status %d' % (i,),
                    ).activity_form))

    def test_usageByOtherApps(self):

        PATH = '/users'
        EXPECTED_SERIALIZATION = [
                {'id': 'https://testserver/users/alice', 'name': 'alice', 'type': 'Person', },
                {'id': 'https://testserver/users/bob', 'name': 'bob', 'type': 'Person', },
                {'id': 'https://testserver/users/carol', 'name': 'carol', 'type': 'Person', },
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
                    'https://testserver/users/alice',
                    'https://testserver/users/bob',
                    'https://testserver/users/carol',
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
                        'https://testserver/users/alice',
                    ],
                     )


