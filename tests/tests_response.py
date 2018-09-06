from django.test import TestCase, Client
from django.test.client import RequestFactory
from django_kepi import TombstoneException
from django_kepi.models import Actor, Following
from django_kepi.responses import *
from things_for_testing.models import ThingUser
from things_for_testing.views import ThingUserCollection
import datetime
import json
import math

EXAMPLE_SERVER = 'http://testserver'
JSON_TYPE = 'application/activity+json'
PAGE_LENGTH = 50

class ResponseTests(TestCase):

    # We are checking:
    #  - TombstoneException (may as well test it here)
    #  - response(various objects)
    #  - response(thing that throws Tombstone)
    #  - default CollectionResponse, passing in items
    #  - CollectionResponse if one of the items is a Tombstone
    #  - specialised CollectionResponses with overridden _transform_item 

    def test_tombstone_exception(self):

        te = TombstoneException(
                fred = 'jim',
                sheila = 'hazel',
                )

        self.assertEqual(
                te.activity,
                {
                    'fred': 'jim',
                    'sheila': 'hazel',
                    'type': 'Tombstone',
                    })

    def test_empty_response(self):

        aor = ActivityObjectResponse()
        self.assertEqual(
                aor.content,
                 b'')

    def test_object_response(self):

        class RandomWeirdThing(object):
            @property
            def activity(self):
                return {
                        'where': 'there',
                        'what': 'that',
                        }

        rwt = RandomWeirdThing()
        aor = ActivityObjectResponse(item=rwt)

        self.assertEqual(aor.status_code, 200)

        content_value = json.loads(aor.content.decode(encoding='UTF-8'))

        self.assertEqual(
                rwt.activity,
                content_value)

    def test_tombstone_object_response(self):

        class RandomWeirdGoneAwayThing(object):
            @property
            def activity(self):
                raise TombstoneException(former_type='Article')

        rwgat = RandomWeirdGoneAwayThing()
        aor = ActivityObjectResponse(item=rwgat)

        self.assertEqual(aor.status_code, 410)

        content_value = json.loads(aor.content.decode(encoding='UTF-8'))
        self.assertEqual(
                {'former_type': 'Article', 'type': 'Tombstone'},
                content_value)

    def test_collection_response(self):

        people = {}

        for name in ['alice', 'albert', 'bob']:
            people[name] = ThingUser(name=name)
            people[name].save()

        PATH_INDEX = '/users/something'
        PATH_PAGE1 = PATH_INDEX+'?page=1'

        rf = RequestFactory()
        request_index = rf.get(PATH_INDEX)
        request_page1 = rf.get(PATH_PAGE1)

        for queryset in [
                ThingUser.objects.none(),
                ThingUser.objects.filter(name='alice'),
                ThingUser.objects.filter(name__startswith='al'),
                ThingUser.objects.all(),
                ]:

            ################ check the index

            cr = CollectionResponse(queryset, request_index)

            self.assertEqual(cr.status_code, 200)

            content_value = json.loads(cr.content.decode(encoding='UTF-8'))

            self.assertEqual(content_value['totalItems'], queryset.count())
            self.assertEqual(content_value['type'], 'OrderedCollection')
            self.assertEqual(content_value['id'], EXAMPLE_SERVER+PATH_INDEX)

            if queryset.count()==0:
                self.assertNotIn('first', content_value)
            else:
                self.assertEqual(content_value['first'], EXAMPLE_SERVER+PATH_PAGE1)

            ################ check the first page

            if queryset.count()==0:
                continue

            cr = CollectionResponse(queryset, request_page1)

            self.assertEqual(cr.status_code, 200)

            content_value = json.loads(cr.content.decode(encoding='UTF-8'))

            self.assertEqual(content_value['totalItems'], queryset.count())
            self.assertEqual(content_value['type'], 'OrderedCollectionPage')
            self.assertEqual(content_value['partOf'], EXAMPLE_SERVER+PATH_INDEX)
            self.assertEqual(content_value['id'], EXAMPLE_SERVER+PATH_PAGE1)

            expectedItems = [x.activity for x in queryset]
            self.assertEqual(content_value['orderedItems'], expectedItems)

    def test_collection_response_spills(self):

        rf = RequestFactory()
        PATH = '/something?page=%d'

        for i in range(1, PAGE_LENGTH*3):
            someone = ThingUser(name='Person %03d' % (i,))
            someone.save()

            expected_page_count = math.ceil(i/PAGE_LENGTH)

            queryset = ThingUser.objects.all()

            for p in range(1, expected_page_count+1):
                request_page = rf.get(PATH % (p,))
                cr = CollectionResponse(queryset, request_page)
                content_value = json.loads(cr.content.decode(encoding='UTF-8'))

                self.assertEqual(content_value['totalItems'], i)
                self.assertEqual(content_value['id'], EXAMPLE_SERVER+PATH % (p,))

                if p==1:
                    self.assertNotIn('prev', content_value)
                else:
                    self.assertEqual(content_value['prev'], EXAMPLE_SERVER+PATH % (p-1))

                if p==expected_page_count:
                    self.assertNotIn('next', content_value)
                else:
                    self.assertEqual(content_value['next'], EXAMPLE_SERVER+PATH % (p+1))

    def test_tombstone_collection_response(self):
        for name in ['King William', 'Queen Anne', 'Queen Elizabeth']:
            # "Queen Anne" is a magic name which causes ThingUser.activity
            # to throw TombstoneException
            # XXX this is not elegant
            someone = ThingUser(name=name)
            someone.save()

        queryset = ThingUser.objects.all()
        rf = RequestFactory()
        request_page = rf.get('/something?page=1')
        cr = CollectionResponse(queryset, request_page)
        content_value = json.loads(cr.content.decode(encoding='UTF-8'))

        self.assertEqual(
                [p['type'] for p in content_value['orderedItems']],
                ['Person', 'Tombstone', 'Person'],
                )

    def test_collection_with_overridden_transform(self):

        for (name, colour) in [
                ('alice', 'blue'),
                ('bob', 'green'),
                ('carol', 'mauve'),
                ]:
            someone = ThingUser(
                    name=name,
                    favourite_colour=colour,
                    )
            someone.save()

        class CollectionColourResponse(CollectionResponse):
            def _transform_object(self, obj):
                return obj.favourite_colour

        queryset = ThingUser.objects.all()
        rf = RequestFactory()
        request_page = rf.get('/something?page=1')
        cr = CollectionColourResponse(queryset, request_page)
        content_value = json.loads(cr.content.decode(encoding='UTF-8'))

        self.assertEqual(
                content_value['orderedItems'],
                ['blue', 'green', 'mauve'],
                )


