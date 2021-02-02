# trilby_api/views/oauth.py
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

def fix_oauth2_redirects():
    """
    Called from kepi.kepi.urls to fix a silly oversight
    in oauth2_provider. This isn't elegant.

    oauth2_provider.http.OAuth2ResponseRedirect checks the
    URL it's redirecting to, and raises DisallowedRedirect
    if it's not a recognised protocol. But this breaks apps
    like Tusky, which registers its own protocol with Android
    and then redirects to that in order to bring itself
    back once authentication's done.

    There's no way to fix this as a user of that package.
    Hence, we have to monkey-patch that class.
    """

    def fake_validate_redirect(not_self, redirect_to):
        return True

    from oauth2_provider.http import OAuth2ResponseRedirect as OA2RR
    OA2RR.validate_redirect = fake_validate_redirect
    logger.info("Monkey-patched %s.", OA2RR)

###########################

class Apps(View):

    def post(self, request, *args, **kwargs):

        new_app = Application(
            name = request.POST['client_name'],
            redirect_uris = request.POST['redirect_uris'],
            client_type = 'confidential',
            authorization_grant_type = 'authorization-code',
            user = None, # don't need to be logged in
            )

        new_app.save()

        result = {
            'id': new_app.id,
            'client_id': new_app.client_id,
            'client_secret': new_app.client_secret,
            }

        return JsonResponse(result)


