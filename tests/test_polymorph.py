from django.test import TestCase
from django_kepi.create import create
from django_kepi.models import *
import logging

logger = logging.getLogger(name='tests')

class TestPolymorph(TestCase):

    def test_invalid_type(self):
        t = create(
                f_type = 'Wombat',
                )
        self.assertIsNone(t)

    def test_note(self):
        t = create(
                f_type = 'Note',
                )
        self.assertIsInstance(t, Item)

    def test_person(self):
        t = create(
                f_type = 'Person',
                )
        self.assertIsInstance(t, Actor)

    def test_abstract(self):
        t = create(
                f_type = 'Object',
                )
        self.assertIsNone(t)

