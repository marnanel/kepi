from django.test import TestCase
from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for accounts. API docs are here:
# https://docs.joinmastodon.org/methods/accounts/

class TestAccountCredentials(TestCase):

    # Getting the list of an account's statuses is handled in test_timeline.

    @skip("Not yet implemented")
    def test_register(self):
        pass

    @skip("Not yet implemented")
    def test_verify_credentials(self):
        pass
    
    @skip("Not yet implemented")
    def test_update_credentials(self):
        pass

    @skip("Not yet implemented")
    def test_get_account(self):
        pass

    @skip("Not yet implemented")
    def test_account_followers(self):
        pass

    @skip("Not yet implemented")
    def test_account_following(self):
        pass

    @skip("Not yet implemented")
    def test_account_in_lists(self):
        pass

    @skip("Not yet implemented")
    def test_account_relationships(self):
        pass

    @skip("Not yet implemented")
    def test_account_search(self):
        pass

class TestAccountActions(TestCase):

    @skip("Not yet implemented")
    def test_follow(self):
        pass

    @skip("Not yet implemented")
    def test_unfollow(self):
        pass

    @skip("Not yet implemented")
    def test_block(self):
        pass

    @skip("Not yet implemented")
    def test_unblock(self):
        pass

    @skip("Not yet implemented")
    def test_mute(self):
        pass

    @skip("Not yet implemented")
    def test_unmute(self):
        pass

