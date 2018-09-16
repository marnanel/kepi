from django.test import TestCase, Client
from django_kepi import NeedToFetchException
from django_kepi.views import InboxView
from django_kepi.models import QuarantinedMessage

class TestInbox(TestCase):

    def test_specific_post(self):

        QuarantinedMessage.objects.all().delete()

        c = Client()

        c.post('/users/alice/inbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "type": "Article",
                    },
                )

        self.assertTrue(
                QuarantinedMessage.objects.filter(username='alice').exists())

    def test_shared_post(self):

        QuarantinedMessage.objects.all().delete()

        c = Client()

        c.post('/sharedInbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "type": "Article",
                    },
                )

        self.assertTrue(
                QuarantinedMessage.objects.filter(username=None).exists())
