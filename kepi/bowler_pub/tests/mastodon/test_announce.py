from django.test import TestCase
from unittest import skip, expectedFailure
import logging

logger = logging.getLogger(name='kepi')

class TestAnnounce(TestCase):
    def test_sender_with_local_follower_boosts_known_status(self):
        pass

    def test_sender_with_local_follower_boosts_unknown_status(self):
        pass

    def test_sender_with_local_follower_selfboosts_unknown_status(self):
        pass

    def test_reblog_of_local_status(self):
        pass

    # TODO relays are not implemented and not tested

    def test_irrelevant(self):
        pass
