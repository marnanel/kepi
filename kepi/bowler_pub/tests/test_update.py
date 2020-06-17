# test_update.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.test import TestCase

class TestUpdate(TestCase):

    """
    Tests for whether we can act on receiving the Update activity.

    Update can theoretically be used on almost any kind of object.
    In practice, we expect it to be used on statuses and persons.

    At present only remote users, not local users, are allowed
    to submit updates over ActivityPub. When local users are
    supported, we need to extend this test: the spec says that
    remote Update activities must supply all the fields whether
    or not they're going to change, but local ones only need
    to supply the fields they're going to change.
    """
    # TODO: see note in docstring about local ActivityPub updates

    # TODO: supporting Update is planned for a later pre-1.0 release
    pass
