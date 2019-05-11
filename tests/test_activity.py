from django.test import TestCase
from django_kepi.models import Activity

FRED_URL = 'https://users.example.com/user/fred'

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
                    "type": "Note",
                    },
                },
                sender="https://remote.example.com")

        with self.assertRaisesMessage(ValueError, "Wrong parameters for Activity type"):
            Activity.create({
                "id": "https://example.com/id/1",
                "type": "Create",
                })
