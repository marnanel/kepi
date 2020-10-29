from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for search. API docs are here:
# https://docs.joinmastodon.org/methods/search/

class Tests(TrilbyTestCase):

    def test_v1(self):
        raise NotImplementedError()

    def test_v2(self):
        raise NotImplementedError()
