from django.test import TestCase
from kepi.bowler_pub.models import Audience
from kepi.bowler_pub.create import create
from . import create_local_person, REMOTE_FRED, REMOTE_JIM

class TestAudience(TestCase):

    def setUp(self):
        self._narcissus = create_local_person(
                name = 'narcissus',
                )

    def test_add_audiences_for(self):

        self._like = create(
                f_type = 'Like',
                f_actor = self._narcissus,
                f_object = self._narcissus,
                run_side_effects = False,
                run_delivery = False,
                )

        a = Audience.add_audiences_for(
                thing = self._like,
                field = 'to',
                value = [
                    REMOTE_FRED,
                    REMOTE_JIM,
                    ],
                )

        results = Audience.objects.filter(
                parent = self._like,
                )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].recipient, REMOTE_FRED)
        self.assertEqual(results[1].recipient, REMOTE_JIM)

    def test_create(self):

        self._like = create(
                f_type = 'Like',
                f_actor = self._narcissus,
                f_object = self._narcissus,
                to = [ REMOTE_FRED, REMOTE_JIM, ],
                run_side_effects = False,
                run_delivery = False,
                )

        results = Audience.objects.filter(
                parent = self._like,
                )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].recipient, REMOTE_FRED)
        self.assertEqual(results[1].recipient, REMOTE_JIM)

    def test_get_audiences_for(self):

        self._like = create(
                f_type = 'Like',
                f_actor = self._narcissus,
                f_object = self._narcissus,
                run_side_effects = False,
                run_delivery = False,
                )

        for fieldname in ['to', 'cc', 'bcc']:
            a = Audience.add_audiences_for(
                    thing = self._like,
                    field = fieldname,
                    value = [
                        REMOTE_FRED,
                        REMOTE_JIM,
                        ],
                    )

        self.assertDictEqual(
                Audience.get_audiences_for(self._like),
                {'to': ['https://remote.example.org/users/fred',
                    'https://remote.example.org/users/jim'],
                    'cc': ['https://remote.example.org/users/fred',
                        'https://remote.example.org/users/jim'],
                    'bcc': ['https://remote.example.org/users/fred',
                        'https://remote.example.org/users/jim'],
                    })

        self.assertDictEqual(
                Audience.get_audiences_for(self._like,
                    hide_blind = True,
                    ),
                {'to': ['https://remote.example.org/users/fred',
                    'https://remote.example.org/users/jim'],
                    'cc': ['https://remote.example.org/users/fred',
                        'https://remote.example.org/users/jim'],
                    })
