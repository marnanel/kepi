# test_signals.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.test import TestCase
from kepi.bowler_pub.create import create
from kepi.bowler_pub.signals import created
from . import create_local_person

class TestSignals(TestCase):

    def test_creation(self):

        self._signal_was_called_with = None
        
        def receiver(sender, value, **kwargs):
            self._signal_was_called_with = value

        created.connect(receiver)

        alice = create_local_person(name='alice')

        self.assertEqual(
                self._signal_was_called_with,
                alice,
                )
