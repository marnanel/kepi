from django.test import TestCase
from django_kepi import find, register_type

class ResolveTests(TestCase):

    def test_find(self):

        class Fruit(object):

            @classmethod
            def activity_find(self, url):
                if url=='https://yellow.example.com':
                    return {'name': 'Banana'}
                elif url=='https://orange.example.com':
                    return {'name': 'Orange'}
                else:
                    return None

        class Tellytubby(object):

            @classmethod
            def activity_find(self, url):
                if url=='https://yellow.example.com':
                    return {'name': 'Laa-Laa'}
                elif url=='https://purple.example.com':
                    return {'name': 'Tinky Winky'}
                else:
                    return None

        register_type('Fruit', Fruit)

        self.assertEqual(find('https://yellow.example.com'),
                {'name': 'Banana'})
        self.assertEqual(find('https://yellow.example.com', 'Fruit'),
                {'name': 'Banana'})
        self.assertEqual(find('https://purple.example.com', 'Fruit'),
                None)
        self.assertEqual(find('https://yellow.example.com', 'Tellytubby'),
                None)
        self.assertEqual(find('https://yellow.example.com', 'TubeLine'),
                None)

        register_type('Tellytubby', Tellytubby)

        self.assertEqual(find('https://yellow.example.com', 'Fruit'),
                {'name': 'Banana'})
        self.assertEqual(find('https://purple.example.com', 'Fruit'),
                None)
        self.assertEqual(find('https://yellow.example.com', 'Tellytubby'),
                {'name': 'Laa-Laa'})
        self.assertEqual(find('https://yellow.example.com', 'TubeLine'),
                None)
        self.assertEqual(find('https://yellow.example.com', ['Tellytubby']),
                {'name': 'Laa-Laa'})
        self.assertEqual(find('https://yellow.example.com', ['Fruit']),
                {'name': 'Banana'})
        self.assertEqual(find('https://yellow.example.com', ['Tellytubby', 'Fruit']),
                {'name': 'Laa-Laa'})
        self.assertEqual(find('https://yellow.example.com', ['Fruit', 'Tellytubby']),
                {'name': 'Banana'})
        self.assertEqual(find('https://yellow.example.com', ['Fruit', 'TubeLine', 'Tellytubby']),
                {'name': 'Banana'})
        self.assertEqual(find('https://purple.example.com', ['Tellytubby', 'Fruit']),
                {'name': 'Tinky Winky'})
        self.assertEqual(find('https://purple.example.com', ['Fruit', 'Tellytubby']),
                {'name': 'Tinky Winky'})
        self.assertEqual(find('https://blue.example.com', ['Tellytubby', 'Fruit']),
                None)
        self.assertEqual(find('https://blue.example.com', ['Fruit', 'Tellytubby']),
                None)
