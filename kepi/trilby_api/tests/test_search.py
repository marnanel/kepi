from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings
from unittest import skip

# Tests for search. API docs are here:
# https://docs.joinmastodon.org/methods/search/

class Tests(TrilbyTestCase):

    @skip("to be implemented later")
    def test_v1(self):
        raise NotImplementedError()

    @skip("to be implemented later")
    def test_v2(self):
        raise NotImplementedError()
