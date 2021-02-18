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

DEFAULT_TIMELINE_SLICE_LENGTH = 20

class AbstractTimeline(generics.ListAPIView):

    serializer_class = StatusSerializer
    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self):
        raise NotImplementedError("cannot query abstract timeline")

    def filter_queryset(self, queryset,
            min_id = None,
            max_id = None,
            since_id = None,
            local = False,
            remote = False,
            limit = DEFAULT_TIMELINE_SLICE_LENGTH,
            *args, **kwargs,
            ):

        logger.debug("Timeline queryset: %s", queryset)

        if 'min_id' in self.request.query_params:
            queryset = queryset.filter(
                    id__gte = int(self.request.query_params['min_id']),
                    )
            logger.debug("  -- after min_id: %s", queryset)

        if 'max_id' in self.request.query_params:
            queryset = queryset.filter(
                    id__lte = int(self.request.query_params['max_id']),
                    )
            logger.debug("  -- after max_id: %s", queryset)

        if 'since_id' in self.request.query_params:
            queryset = queryset.filter(
                    id__gt = int(self.request.query_params['since_id']),
                    )
            logger.debug("  -- after since_id: %s", queryset)

        if 'local' in self.request.query_params:
            queryset = queryset.filter(
                    remote_url__isnull = \
                            bool(self.request.query_params['local']),
                    )
            logger.debug("  -- after local: %s", queryset)

        if 'remote' in self.request.query_params:
            queryset = queryset.filter(
                    remote_url__isnull = \
                            not bool(self.request.query_params['remote']),
                    )
            logger.debug("  -- after remote: %s", queryset)

        if 'only_media' in self.request.query_params:
            # We don't support media at present, so this will give us
            # the empty set
            queryset = queryset.none()
            logger.debug("  -- after only_media: %s", queryset)

        # Slicing the queryset must be done last,
        # since running operations on a sliced queryset
        # causes evaluation.
        limit = int(self.request.query_params.get('limit',
                default = DEFAULT_TIMELINE_SLICE_LENGTH,
                ))

        queryset = queryset[:limit]

        logger.debug("  -- after slice of %d: %s",
                limit,
                queryset,
                )

        return queryset

class PublicTimeline(AbstractTimeline):

    permission_classes = ()

    def get_queryset(self):

        result = trilby_models.Status.objects.filter(
                visibility = trilby_utils.VISIBILITY_PUBLIC,
                )

        return result

class HomeTimeline(AbstractTimeline):

    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self):

        result = self.request.user.localperson.inbox

        logger.debug("Home timeline is %s",
                result)

        return result

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
