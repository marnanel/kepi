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
                "actor": "https://example.com/user/fred",
                "object": {
                    "type": "Article",
                    },
                },
                sender="https://remote.example.com")

        with self.assertRaisesMessage(ValueError, "Wrong parameters for type"):
            Activity.create({
                "id": "https://example.com/id/1",
                "type": "Create",
                })

        fred = ThingUser(name="fred")
        fred.save()
