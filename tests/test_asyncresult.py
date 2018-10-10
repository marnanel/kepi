from django.test import TestCase, Client
from django_kepi.models import Activity, QuarantinedMessage, QuarantinedMessageNeeds
from django_kepi import create, resolve
from things_for_testing import KepiTestCase
import logging
import httpretty
import json

logger = logging.Logger(name=__name__)

class TestAsyncResult(KepiTestCase):

    @httpretty.activate
    def test_simple(self):
        
        PERSON_URL = 'https://example.net/polly'
        ARTICLE_URL = 'https://example.com/articles/kettles-are-nice'
        
        polly = create({
            'id': PERSON_URL,
            'type': 'Person',
            })

        QUARANTINED_BODY = json.dumps({
            "id": "https://example.com/id/1",
            "type": "Like",
            "actor": PERSON_URL,
            "object": ARTICLE_URL,
            })

        self._mock_remote_object(PERSON_URL, ftype='Person')
        self._mock_remote_object(ARTICLE_URL, ftype='Article')

        qlike = QuarantinedMessage(
                username=None,
                headers='',
                body=QUARANTINED_BODY,
            )
        qlike.save()
        qlike.deploy()

        c = Client()

        need_article_uuid = QuarantinedMessageNeeds.objects.get(needs_to_fetch=ARTICLE_URL).id

        c.post('/asyncResult?success=True&uuid=%s' % (need_article_uuid,),
                content_type = 'application/activity+json',
                data = {
                    'id': ARTICLE_URL,
                    "type": "Article",
                    "title": "Kettles are nice",
                    },
                )

        self.assertFalse(
                QuarantinedMessage.objects.filter(body=QUARANTINED_BODY).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=ARTICLE_URL).exists())

        self.assertIsNone(
                resolve(
                    identifier=ARTICLE_URL,
                    ))

    @httpretty.activate
    def test_partial(self):
        
        PERSON_URL = 'https://example.net/mary'
        ARTICLE_URL = 'https://example.com/articles/lambs-are-nice'
        QUARANTINED_BODY = json.dumps({
            "id": "https://example.com/id/2",
            "type": "Like",
            "actor": PERSON_URL,
            "object": ARTICLE_URL,
            })

        self._mock_remote_object(PERSON_URL, ftype='Person')
        self._mock_remote_object(ARTICLE_URL, ftype='Article')

        qlike = QuarantinedMessage(
                username=None,
                headers='',
                body=QUARANTINED_BODY,
            )
        qlike.save()
        qlike.deploy()

        c = Client()

        need_article_uuid = QuarantinedMessageNeeds.objects.get(needs_to_fetch=ARTICLE_URL).id

        c.post('/asyncResult?success=True&uuid=%s' % (need_article_uuid,),
                content_type = 'application/activity+json',
                data = {
                    'id': ARTICLE_URL,
                    "type": "Article",
                    "title": "Lambs are nice",
                    },
                )

        self.assertTrue(
                QuarantinedMessage.objects.filter(body=QUARANTINED_BODY).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=ARTICLE_URL).exists())
        self.assertTrue(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=PERSON_URL).exists())

        need_person_uuid = QuarantinedMessageNeeds.objects.get(needs_to_fetch=PERSON_URL).id

        c.post('/asyncResult?success=True&uuid=%s' % (need_person_uuid,),
                content_type = 'application/activity+json',
                data = {
                    'id': PERSON_URL,
                    "type": "Person",
                    },
                )

        self.assertFalse(
                QuarantinedMessage.objects.filter(body=QUARANTINED_BODY).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=ARTICLE_URL).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=PERSON_URL).exists())

        # XXX assert that the activity now exists

    @httpretty.activate
    def test_failure(self):
        
        PERSON_URL = 'https://example.net/lucy'
        ARTICLE_URL = 'https://example.com/articles/losing-your-pocket'
        QUARANTINED_BODY = """{
            "id": "https://example.com/id/3",
            "type": "Like",
            "actor": "%s",
            "object": "%s"
            }""" % (PERSON_URL, ARTICLE_URL,)

        self._mock_remote_object(PERSON_URL, ftype='Person', status=404)
        self._mock_remote_object(ARTICLE_URL, ftype='Article')

        # XXX For some reason, this allows Celery to
        # access /async_result in the test version;
        # without it, the socket library throws an error.
        httpretty.register_uri(
                httpretty.POST,
                'https://localhost/async_result',
                body='something')

        qlike = QuarantinedMessage(
                username=None,
                headers='',
                body=QUARANTINED_BODY,
            )
        qlike.save()
        qlike.deploy()

        c = Client()

        need_article_uuid = QuarantinedMessageNeeds.objects.get(needs_to_fetch=ARTICLE_URL).id

        c.post('/asyncResult?success=True&uuid=%s' % (need_article_uuid,),
                content_type = 'application/activity+json',
                data = {
                    'id': ARTICLE_URL,
                    "type": "Article",
                    "title": "Losing your pocket",
                    },
                )

        self.assertTrue(
                QuarantinedMessage.objects.filter(body=QUARANTINED_BODY).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=ARTICLE_URL).exists())
        self.assertTrue(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=PERSON_URL).exists())

        # But the person check fails!
        need_person_uuid = QuarantinedMessageNeeds.objects.get(needs_to_fetch=PERSON_URL).id

        c.post('/asyncResult?success=False&uuid=%s' % (need_person_uuid,),
                )

        self.assertFalse(
                QuarantinedMessage.objects.filter(body=QUARANTINED_BODY).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=ARTICLE_URL).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=PERSON_URL).exists())

        # XXX assert that the activity does NOT exist

