from django.test import TestCase, Client
from django_kepi.models import Activity, QuarantinedMessage, QuarantinedMessageNeeds
from django_kepi import create, resolve

# XXX bug is:
# XXX   attempts to redeploy cause duplicate "needs" records

class TestAsyncResult(TestCase):

    def test_simple(self):
        
        polly = create({
            'id': 'https://example.net/polly',
            'type': 'Person',
            })

        ARTICLE_URL = 'https://example.com/articles/kettles-are-nice'
        QUARANTINED_BODY = """{
            "id": "https://example.com/id/1",
            "type": "Like",
            "actor": "https://example.net/polly",
            "object": "%s"
            }""" % (ARTICLE_URL,)

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

    def test_partial(self):
        
        PERSON_URL = 'https://example.net/mary'
        ARTICLE_URL = 'https://example.com/articles/lambs-are-nice'
        QUARANTINED_BODY = """{
            "id": "https://example.com/id/2",
            "type": "Like",
            "actor": "%s",
            "object": "%s"
            }""" % (PERSON_URL, ARTICLE_URL,)

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

    def test_failure(self):
        
        PERSON_URL = 'https://example.net/lucy'
        ARTICLE_URL = 'https://example.com/articles/losing-your-pocket'
        QUARANTINED_BODY = """{
            "id": "https://example.com/id/3",
            "type": "Like",
            "actor": "%s",
            "object": "%s"
            }""" % (PERSON_URL, ARTICLE_URL,)

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
