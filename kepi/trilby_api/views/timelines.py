# trilby_api/views/timelines.py
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


class AbstractTimeline(generics.ListAPIView):

    serializer_class = StatusSerializer
    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self, request):
        raise NotImplementedError("cannot query abstract timeline")

    def get(self, request):
        queryset = self.get_queryset(request)
        serializer = self.serializer_class(queryset,
                many = True,
                context = {
                    'request': request,
                    })
        return Response(serializer.data)

PUBLIC_TIMELINE_SLICE_LENGTH = 20

class PublicTimeline(AbstractTimeline):

    permission_classes = ()

    def get_queryset(self, request):

        result = trilby_models.Status.objects.filter(
                visibility = trilby_utils.VISIBILITY_PUBLIC,
                )[:PUBLIC_TIMELINE_SLICE_LENGTH]

        return result

class HomeTimeline(AbstractTimeline):

    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self, request):

        result = request.user.localperson.inbox

        logger.debug("Home timeline is %s",
                result)

        return result

########################################

########################################

class UserFeed(View):

    permission_classes = ()

    def get(self, request, username, *args, **kwargs):

        try:
            the_person = get_object_or_404(
                    self.get_queryset(),
                    id = int(kwargs['user']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        context = {
                'self': request.build_absolute_uri(),
                'user': the_person,
                'statuses': the_person.outbox,
                'server_name': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
            }

        result = render(
                request=request,
                template_name='account.atom.xml',
                context=context,
                content_type='application/atom+xml',
                )

        links = ', '.join(
                [ '<{}>; rel="{}"; type="{}"'.format(
                    settings.KEPI[uri].format(
                        hostname = settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                        username = the_person.id[1:],
                        ),
                    rel, mimetype)
                    for uri, rel, mimetype in
                    [
                        ('USER_WEBFINGER_URLS',
                            'lrdd',
                            'application/xrd+xml',
                            ),

                        ('USER_FEED_URLS',
                            'alternate',
                            'application/atom+xml',
                            ),

                        ('USER_FEED_URLS',
                            'alternate',
                            'application/activity+json',
                            ),
                        ]
                    ])

        result['Link'] = links

        return result
