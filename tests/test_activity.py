from django.test import TestCase
from django_kepi.models import Activity

class TestActivity(TestCase):

    def test_parameters(self):

        with self.assertRaisesMessage(ValueError, "is not an Activity type"):
                Activity.deserialize({
                    "id": "https://example.com/id/1",
                    "type": "Wombat",
                    })
