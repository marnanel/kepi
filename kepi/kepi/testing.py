import logging
import sys
import django

logger = logging.getLogger('kepi')

class KepiTestCase(django.test.TestCase):
    """
    A test case.

    It turns on logging to stdout.
    """

    def setUp(self):
        super().setUp()
        self._logging_stream_handler = logging.StreamHandler(sys.stdout)
        logger.addHandler(self._logging_stream_handler)

    def tearDown(self):
        super().tearDown()
        logger.removeHandler(self._logging_stream_handler)
