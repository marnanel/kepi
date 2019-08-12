from django.test import TestCase
from django_kepi.models import Audience
from django_kepi.create import create
from . import create_local_person, REMOTE_FRED, REMOTE_JIM

class TestAudience(TestCase):
    
    def test_add_audiences_for(self):
        narcissus = create_local_person(
                name = 'narcissus',
                )

        like = create(
                f_type = 'Like',
                f_actor = narcissus,
                f_object = narcissus,
                )

        a = Audience.add_audiences_for(
                thing = like,
                field = 'to',
                value = [
                    REMOTE_FRED,
                    REMOTE_JIM,
                    ],
                )

        results = Audience.objects.filter(
                parent = like,
                )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].recipient, REMOTE_FRED)
        self.assertEqual(results[1].recipient, REMOTE_JIM)

    def test_create(self):
        narcissus = create_local_person(
                name = 'narcissus',
                )

        like = create(
                f_type = 'Like',
                f_actor = narcissus,
                f_object = narcissus,
                to = [ REMOTE_FRED, REMOTE_JIM, ],
                )

        results = Audience.objects.filter(
                parent = like,
                )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].recipient, REMOTE_FRED)
        self.assertEqual(results[1].recipient, REMOTE_JIM)

    def test_get_audiences_for(self):
        narcissus = create_local_person(
                name = 'narcissus',
                )

        like = create(
                f_type = 'Like',
                f_actor = narcissus,
                f_object = narcissus,
                )

        for fieldname in ['to', 'cc', 'bcc']:
            a = Audience.add_audiences_for(
                    thing = like,
                    field = fieldname,
                    value = [
                        REMOTE_FRED,
                        REMOTE_JIM,
                        ],
                    )

        self.assertDictEqual(
                Audience.get_audiences_for(like),
                {'to': ['https://remote.example.org/users/fred',
                    'https://remote.example.org/users/jim'],
                    'cc': ['https://remote.example.org/users/fred',
                        'https://remote.example.org/users/jim'],
                    'bcc': ['https://remote.example.org/users/fred',
                        'https://remote.example.org/users/jim'],
                    })

        self.assertDictEqual(
                Audience.get_audiences_for(like,
                    hide_blind = True,
                    ),
                {'to': ['https://remote.example.org/users/fred',
                    'https://remote.example.org/users/jim'],
                    'cc': ['https://remote.example.org/users/fred',
                        'https://remote.example.org/users/jim'],
                    })



