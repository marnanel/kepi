from django.test import TestCase
from django_kepi import resolve

class ResolveTests(TestCase):

    def test_resolve(self):
        r = resolve('https://example.com/something')
        # XXX ...
