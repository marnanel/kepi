from django.test import TestCase
from django_kepi.models import Thing

REMOTE_ID_1 = 'https://users.example.com/activity/1'

REMOTE_FRED = 'https://users.example.com/user/fred'

SAMPLE_NOTE = {
        "type": "Note",
        }

class TestThing(TestCase):

    def test_bad_type(self):

        with self.assertRaisesMessage(ValueError, "is not a thing type"):
            Thing.create({
                "id": REMOTE_ID_1,
                "type": "Wombat",
                })

    def test_remote_no_id(self):

        with self.assertRaisesMessage(ValueError, "Remote things must have an id"):
            Thing.create({
                "type": "Create",
                "actor": "https://example.com/user/fred",
                "object": {
                    "type": "Note",
                    },
                },
                sender="https://remote.example.com")

    def test_create_create_wrong_params(self):

        with self.assertRaisesMessage(ValueError, "Wrong parameters for thing type"):
            Thing.create({
                "id": REMOTE_ID_1,
                "type": "Create",
                })

        with self.assertRaisesMessage(ValueError, "Wrong parameters for thing type"):
            Thing.create({
                "id": REMOTE_ID_1,
                "actor": REMOTE_FRED,
                "type": "Create",
                })

        with self.assertRaisesMessage(ValueError, "Wrong parameters for thing type"):
            Thing.create({
                "id": REMOTE_ID_1,
                "target": REMOTE_FRED,
                "type": "Create",
                })

    def test_create_create(self):
        Thing.create({
            "id": REMOTE_ID_1,
            "type": "Create",
            "actor": REMOTE_FRED,
            "object": SAMPLE_NOTE,
            })

        self.assertEqual(
                Thing.objects.filter(remote_url=REMOTE_ID_1).count(),
                1,
                )
