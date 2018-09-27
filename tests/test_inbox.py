from django.test import TestCase, Client
from django_kepi.views import InboxView
from django_kepi.models import QuarantinedMessage, QuarantinedMessageNeeds
from things_for_testing.models import ThingArticle, ThingUser

class TestInbox(TestCase):

    def test_specific_post(self):

        QuarantinedMessage.objects.all().delete()

        c = Client()

        c.post('/users/alice/inbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "actor": "https://users.example.net/mary",
                    "object": "https://things.example.org/lamb",
                    "type": "Like",
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
                    "actor": "https://users.example.net/mary",
                    "object": "https://things.example.org/lamb",
                    "type": "Like",
                    },
                )

        self.assertTrue(
                QuarantinedMessage.objects.filter(username=None).exists())

    def test_non_json(self):

        QuarantinedMessage.objects.all().delete()

        c = Client()

        c.post('/sharedInbox',
                content_type = 'text/plain',
                data = 'Hello',
                )

        self.assertFalse(
                QuarantinedMessage.objects.all().exists())

    def test_malformed_json(self):

        QuarantinedMessage.objects.all().delete()

        c = Client()

        text = """{
                    "id": "https://example.net/hello-world",
                    "actor": "https://users.example.net/mary",
                    "object": "https://things.example.org/lamb",
                    "type": "Like"
                    }"""

        c.post('/sharedInbox',
                content_type = 'application/activity+json',
                data = text,
                )

        self.assertTrue(
                QuarantinedMessage.objects.all().exists())

        QuarantinedMessage.objects.all().delete()

        text = text[1:] # remove leading {, so the JSON is invalid

        c.post('/sharedInbox',
                content_type = 'application/activity+json',
                data = text,
                )

        self.assertFalse(
                QuarantinedMessage.objects.all().exists())

    def test_all_parts_known(self):

        user = ThingUser(name="margaret")
        user.save()
        article = ThingArticle(title="dragons")
        article.save()

        QuarantinedMessage.objects.all().delete()

        c = Client()

        c.post('/users/alice/inbox',
                content_type = 'application/activity+json',
                data = {
                    "id": "https://example.net/hello-world",
                    "actor": user.activity_id,
                    "object": article.activity_id,
                    "type": "Like",
                    },
                )

        # This should go through immediately, because
        # all parts are known and verifiable.

        self.assertFalse(
                QuarantinedMessage.objects.all().exists())


