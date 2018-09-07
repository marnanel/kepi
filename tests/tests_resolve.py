from django.test import TestCase
from django_kepi import resolve, register_type

class ResolveTests(TestCase):

    def test_resolve(self):

        class Fruit(object):

            @classmethod
            def find_activity(self, url):
                if url=='https://yellow.example.com':
                    return {'name': 'Banana'}
                elif url=='https://orange.example.com':
                    return {'name': 'Orange'}
                else:
                    return None

        class Tellytubby(object):

            @classmethod
            def find_activity(self, url):
                if url=='https://yellow.example.com':
                    return {'name': 'Laa-Laa'}
                elif url=='https://purple.example.com':
                    return {'name': 'Tinky Winky'}
                else:
                    return None

        register_type('Fruit', Fruit)

        self.assertEqual(resolve('https://yellow.example.com'),
                {'name': 'Banana'})
        self.assertEqual(resolve('https://yellow.example.com', 'Fruit'),
                {'name': 'Banana'})
        self.assertEqual(resolve('https://purple.example.com', 'Fruit'),
                None)
        self.assertEqual(resolve('https://yellow.example.com', 'Tellytubby'),
                None)
        self.assertEqual(resolve('https://yellow.example.com', 'TubeLine'),
                None)

        register_type('Tellytubby', Tellytubby)

        self.assertEqual(resolve('https://yellow.example.com', 'Fruit'),
                {'name': 'Banana'})
        self.assertEqual(resolve('https://purple.example.com', 'Fruit'),
                None)
        self.assertEqual(resolve('https://yellow.example.com', 'Tellytubby'),
                {'name': 'Laa-Laa'})
        self.assertEqual(resolve('https://yellow.example.com', 'TubeLine'),
                None)
        self.assertEqual(resolve('https://yellow.example.com', ['Tellytubby']),
                {'name': 'Laa-Laa'})
        self.assertEqual(resolve('https://yellow.example.com', ['Fruit']),
                {'name': 'Banana'})
        self.assertEqual(resolve('https://yellow.example.com', ['Tellytubby', 'Fruit']),
                {'name': 'Laa-Laa'})
        self.assertEqual(resolve('https://yellow.example.com', ['Fruit', 'Tellytubby']),
                {'name': 'Banana'})
        self.assertEqual(resolve('https://yellow.example.com', ['Fruit', 'TubeLine', 'Tellytubby']),
                {'name': 'Banana'})
        self.assertEqual(resolve('https://purple.example.com', ['Tellytubby', 'Fruit']),
                {'name': 'Tinky Winky'})
        self.assertEqual(resolve('https://purple.example.com', ['Fruit', 'Tellytubby']),
                {'name': 'Tinky Winky'})
        self.assertEqual(resolve('https://blue.example.com', ['Tellytubby', 'Fruit']),
                None)
        self.assertEqual(resolve('https://blue.example.com', ['Fruit', 'Tellytubby']),
                None)
