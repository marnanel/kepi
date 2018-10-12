from django.test import TestCase
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

        fred = ThingUser(name="fred")
        fred.save()

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

        created = Activity.create(test_activity)
        self.assertEqual(created, None)

        fred = ThingUser(name="fred")
        fred.save()

        created = Activity.create(test_activity)
        self.assertEqual(created, None)

        article = ThingArticle(title="bananas")
        article.save()

        self.assertIsNotNone(
            Activity.create(test_activity),
            )

