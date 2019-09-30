from django.test import TestCase, Client
from . import create_local_person
from django.conf import settings
import logging

MIME_TYPE = 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'

class TestHeaders(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def test_link(self):

        alice = create_local_person('alice')
        client = Client()
        alice_url = settings.KEPI['USER_URL_FORMAT'] % {
                'username': 'alice',
                'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                }

        response = client.get(alice_url,
                HTTP_ACCEPT = MIME_TYPE,
                )

        links = response['Link'].split(', ')

        self.assertEqual(
                links,
                [
                    '<https://testserver/.well-known/webfinger?resource='+\
                    'acct%3Aalice%40testserver>; rel="lrdd"; '+\
                    'type="application/xrd+xml"',

                    '<https://testserver/users/alice>; '+\
                    'rel="alternate"; type="application/activity+json"',
                    ])
