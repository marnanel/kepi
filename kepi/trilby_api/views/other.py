# trilby_api/views/other.py
#
# Part of kepi.
# Copyright (c) 2018-2021 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.db import IntegrityError, transaction
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import SuspiciousOperation
from django.conf import settings
import kepi.trilby_api.models as trilby_models
import kepi.trilby_api.utils as trilby_utils
from kepi.trilby_api.serializers import *
from rest_framework import generics, response, mixins
from rest_framework.permissions import IsAuthenticated, \
        IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
import kepi.trilby_api.receivers
from kepi.bowler_pub.utils import uri_to_url
import json
import re
import random

class Instance(View):

    def get(self, request, *args, **kwargs):

        result = {
            'uri': 'http://127.0.0.1',
            'title': settings.KEPI['INSTANCE_NAME'],
            'description': settings.KEPI['INSTANCE_DESCRIPTION'],
            'email': settings.KEPI['CONTACT_EMAIL'],
            'version': '1.0.0', # of the protocol
            'urls': {},
            'languages': settings.KEPI['LANGUAGES'],
            'contact_account': settings.KEPI['CONTACT_ACCOUNT'],
            }

        return JsonResponse(result)

class Emojis(View):
    # FIXME
    def get(self, request, *args, **kwargs):
        return JsonResponse([],
                safe=False)

class Filters(View):
    # FIXME
    def get(self, request, *args, **kwargs):
        return JsonResponse([],
                safe=False)

class Search(View):

    # FIXME

    permission_classes = [
            IsAuthenticated,
            ]

    def get(self, request, *args, **kwargs):

        result = {
                'accounts': [],
                'statuses': [],
                'hashtags': [],
            }

        return JsonResponse(result)

class AccountsSearch(generics.ListAPIView):

    # FIXME

    queryset = trilby_models.Person.objects.all()
    serializer_class = UserSerializer

    permission_classes = [
            IsAuthenticated,
            ]
