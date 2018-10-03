from django.test import TestCase, Client
from django_kepi.models import Activity, QuarantinedMessage, QuarantinedMessageNeeds
from django_kepi import create

class TestAsyncResult(TestCase):

    def test_simple(self):
        
        mary = create({
            'id': 'https://example.net/mary',
            'type': 'Person',
            })

        ARTICLE_URL = 'https://example.com/articles/lambs-are-nice'
        QUARANTINED_BODY = """{
            "id": 'https://example.com/id/1',
            "type": 'Like',
            "actor": 'https://example.net/mary',
            "object": '%s',
            }""" % (ARTICLE_URL,)

        qlike = QuarantinedMessage(
                username=None,
                headers='',
                body=QUARANTINED_BODY,
            )
        qlike.save()

        need = QuarantinedMessageNeeds(
                message = qlike,
                needs_to_fetch = ARTICLE_URL,
                )
        need.save()

        c = Client()

        c.post('/asyncResult?success=True&uuid=%s' % (need.id,),
                content_type = 'application/activity+json',
                data = {
                    'id': ARTICLE_URL,
                    "type": "Article",
                    "title": "Lambs are nice",
                    },
                )

        self.assertFalse(
                QuarantinedMessage.objects.filter(body=QUARANTINED_BODY).exists())
        self.assertFalse(
                QuarantinedMessageNeeds.objects.filter(needs_to_fetch=ARTICLE_URL).exists())

