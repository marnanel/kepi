from django.test import TestCase
from django_kepi import NeedToFetchException
from django_kepi.models import Activity
from things_for_testing.models import ThingArticle, ThingUser

class TestActivity(TestCase):

    def test_parameters(self):

        with self.assertRaisesMessage(ValueError, "is not an Activity type"):
            Activity.create({
                "id": "https://example.com/id/1",
                "type": "Wombat",
                })

        with self.assertRaisesMessage(ValueError, "Remote activities must have an id"):
            Activity.create({
                "type": "Create",
                })

        with self.assertRaisesMessage(ValueError, "Wrong parameters for type"):
            Activity.create({
                "id": "https://example.com/id/1",
                "type": "Create",
                })

        with self.assertRaisesMessage(ValueError, "Explicit objects must have an id"):
            Activity.create({
                "id": "https://example.com/id/1",
                "type": "Create",
                "actor": "https://example.com/user/fred",
                "object": {
                    "type": "Article",
                    }
                })

    def test_fetching(self):

        test_activity = {
                "id": "https://example.com/id/1",
                "type": "Create",
                "actor": "https://example.com/user/fred",
                "object": {
                    "id": "https://articles.example.com/bananas",
                    "type": "Article",
                    }
                }

        with self.assertRaises(NeedToFetchException):
            Activity.create(test_activity)

        fred = ThingUser(name="fred")
        fred.save()

        with self.assertRaisesMessage(NeedToFetchException, "https://articles.example.com/bananas"):
            Activity.create(test_activity)

        article = ThingArticle(title="bananas")
        article.save()

        self.assertIsNotNone(
            Activity.create(test_activity),
            )

