# test_delete.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.test import TestCase
import logging

logger = logging.getLogger(name='kepi')

class TestDelete(TestCase):

    """
    Tests for whether we can act on receiving the Delete activity.
    """

    # TODO: supporting Delete is planned for a later pre-1.0 release
    pass
