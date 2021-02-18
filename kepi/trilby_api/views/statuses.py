# trilby_api/views/statuses.py
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
from oauth2_provider.models import Application
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

###########################

def error_response(status, reason):
    return JsonResponse(
            {
                "error": reason,
                },
            status = status,
            reason = reason,
            )

###########################

class DoSomethingWithStatus(generics.GenericAPIView):

    serializer_class = StatusSerializer
    queryset = trilby_models.Status.objects.all()

    def _do_something_with(self, the_status, request):
        raise NotImplementedError()

    def post(self, request, *args, **kwargs):

        if request.user is None:
            logger.debug('  -- user not logged in')
            return error_response(401, 'Not logged in')

        try:
            the_status = get_object_or_404(
                    self.get_queryset(),
                    id = int(kwargs['status']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        result = self._do_something_with(the_status, request)

        if result is None:
            result = the_status

        serializer = StatusSerializer(
                result,
                context = {
                    'request': request,
                    },
                )

        return JsonResponse(
                serializer.data,
                status = 200,
                reason = 'Done',
                )

class Favourite(DoSomethingWithStatus):

    def _do_something_with(self, the_status, request):

        try:
            like = trilby_models.Like(
                liker = request.user.localperson,
                liked = the_status,
                )

            with transaction.atomic():
                like.save(
                        send_signal = True,
                        )

            logger.info('  -- created a Like')

        except IntegrityError:
            logger.info('  -- not creating a Like; it already exists')

class Unfavourite(DoSomethingWithStatus):

    def _do_something_with(self, the_status, request):

        try:
            like = trilby_models.Like.objects.get(
                liker = request.user.localperson,
                liked = the_status,
                )

            logger.info('  -- deleting the Like: %s',
                    like)

            like.delete()

        except trilby_models.Like.DoesNotExist:
            logger.info('  -- not unliking; the Like doesn\'t exists')

class Reblog(DoSomethingWithStatus):

    def _do_something_with(self, the_status, request):

        # Mastodon allows a "visibility" param here
        # but currently doesn't use it in the UI

        # Mastodon doesn't say whether a user can
        # reblog the same status more than once:
        # https://github.com/tootsuite/mastodon/issues/13479
        # For now, I'm assuming that you can.

        content_source = 'RT {}'.format(the_status.content_source)

        new_status = trilby_models.Status(

                # Fields which are different in a reblog:
                account = request.user.localperson,
                content_source = content_source,
                reblog_of = the_status,

                # Fields which are just copied in:
                sensitive = the_status.sensitive,
                spoiler_source = the_status.spoiler_source,
                visibility = the_status.visibility,
                language = the_status.language,
                in_reply_to = the_status.in_reply_to,
                )

        with transaction.atomic():
            new_status.save(
                    send_signal = True,
                    )

        logger.info('  -- created a reblog')

        return new_status

class Unreblog(DoSomethingWithStatus):

    def _do_something_with(self, the_status, request):

        # See the note in "Reblog" about whether
        # multiple reblogs of the same status
        # are allowed.

        reblogs = trilby_models.Status.objects.filter(
                reblog_of = the_status,
                account = request.user.localperson,
                )

        if not reblogs.exists():
            raise Http404("No such reblog")

        reblogs.delete()

        logger.info('  -- deleting reblogs')

###########################

class DoSomethingWithPerson(generics.GenericAPIView):

    serializer_class = UserSerializer
    queryset = trilby_models.Person.objects.all()

    def _do_something_with(self, the_person, request):
        raise NotImplementedError()

    def post(self, request, *args, **kwargs):

        if request.user is None:
            logger.debug('  -- user not logged in')
            return error_response(401, 'Not logged in')

        try:
            the_person = get_object_or_404(
                    self.get_queryset(),
                    id = int(kwargs['user']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        result = self._do_something_with(the_person, request)

        if result is None:
            result = the_person

        serializer = UserSerializer(
                result,
                context = {
                    'request': request,
                    },
                )

        return JsonResponse(
                serializer.data,
                status = 200,
                reason = 'Done',
                )

class Follow(DoSomethingWithPerson):

    def _do_something_with(self, the_person, request):

        try:

            if the_person.auto_follow:
                offer = None
            else:
                number = random.randint(0, 0xffffffff)
                offer = uri_to_url(settings.KEPI['FOLLOW_REQUEST_LINK'] % {
                    'username': request.user.username,
                    'number': number,
                    })

            follow = trilby_models.Follow(
                follower = request.user.localperson,
                following = the_person,
                offer = offer,
                )

            with transaction.atomic():
                follow.save(
                        send_signal = True,
                        )

            logger.info('  -- follow: %s', follow)
            logger.debug('    -- offer ID: %s', offer)

            if the_person.auto_follow:
                follow_back = trilby_models.Follow(
                    follower = the_person,
                    following = request.user.localperson,
                    offer = None,
                    )

                with transaction.atomic():
                    follow_back.save(
                            send_signal = True,
                            )

                logger.info('  -- follow back: %s', follow_back)

            return the_person

        except IntegrityError:
            logger.info('  -- not creating a follow; it already exists')

class Unfollow(DoSomethingWithPerson):

    def _do_something_with(self, the_person, request):

        try:
            follow = trilby_models.Follow.objects.get(
                follower = request.user.localperson,
                following = the_person,
                )

            logger.info('  -- unfollowing: %s', follow)

            with transaction.atomic():
                follow.delete(
                    send_signal = True,
                    )

            return the_person

        except trilby_models.Follow.DoesNotExist:
            logger.info('  -- not unfollowing; they weren\'t following '+\
                    'in the first place')

class SpecificStatus(generics.GenericAPIView):

    queryset = trilby_models.Status.objects.filter(remote_url=None)
    serializer_class = StatusSerializer
    lookup_field = 'status'
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):

        the_status = get_object_or_404(
                self.get_queryset(),
                id = int(kwargs['status']),
                )

        serializer = StatusSerializer(
                the_status,
                context = {
                    'request': request,
                    },
                )

        response = JsonResponse(serializer.data)

        return response

    def delete(self, request, *args, **kwargs):

        if 'status' not in kwargs:
            return error_response(404, 'Can\'t delete all statuses at once')

        the_status = get_object_or_404(
                self.get_queryset(),
                id = int(kwargs['status']),
                )

        if the_status.account != request.user.localperson:
            return error_response(404, # sic
                    'That isn\'t yours to delete')

        serializer = StatusSerializer(
                the_status,
                context = {
                    'request': request,
                    },
                )

        response = JsonResponse(serializer.data)

        the_status.delete()

        return response

class Statuses(generics.ListCreateAPIView,
        ):

    queryset = trilby_models.Status.objects.filter(remote_url=None)
    serializer_class = StatusSerializer

    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        try:
            the_person = get_object_or_404(
                    trilby_models.Person,
                    id = int(kwargs['user']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        logger.info('Looking up all visible statuses, for %s',
               the_person)

        queryset = self.get_queryset().filter(
                account = the_person,
                )

        serializer = StatusSerializer(
                queryset,
                context = {
                    'request': request,
                    },
                many = True,
                )

        return JsonResponse(serializer.data,
                safe = False, # it's a list
                )

    def create(self, request, *args, **kwargs):

        data = request.data

        if 'status' not in data and 'media_ids' not in data:
            return HttpResponse(
                    status = 400,
                    content = 'You must supply a status or some media IDs',
                    )

        status = trilby_models.Status(
                account = request.user.localperson,
                content_source = data.get('status', ''),
                sensitive = data.get('sensitive', False),
                spoiler_source = data.get('spoiler_text', ''),
                visibility = data.get('visibility', 'public'),
                language = data.get('language',
                    settings.KEPI['LANGUAGES'][0]),
                # FIXME: in_reply_to
                # FIXME: media_ids
                # FIXME: idempotency_key
                )

        status.save(
                send_signal = True,
                )

        serializer = StatusSerializer(
                status,
                partial = True,
                context = {
                    'request': request,
                    },
                )

        return JsonResponse(
                serializer.data,
                status = 200, # should really be 201 but the spec says 200
                reason = 'Hot off the press',
                )


class StatusContext(generics.ListCreateAPIView):

    queryset = trilby_models.Status.objects.all()

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        status = queryset.get(id=int(kwargs['status']))
        serializer = StatusContextSerializer(status)

        return JsonResponse(serializer.data)

class StatusFavouritedBy(generics.ListCreateAPIView):

    queryset = trilby_models.Person.objects.all()

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        status = trilby_models.Status.objects.get(id=int(kwargs['status']))

        status.save()

        people = queryset.filter(
                like__liked = status,
                )

        serializer = UserSerializer(people,
                many=True)

        return JsonResponse(serializer.data,
                safe=False, # it's a list
                )

class StatusRebloggedBy(generics.ListCreateAPIView):

    queryset = trilby_models.Person.objects.all()

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        status = trilby_models.Status.objects.get(id=int(kwargs['status']))

        people = queryset.filter(
                poster__reblog_of = status,
                )

        serializer = UserSerializer(people,
                many=True)

        return JsonResponse(serializer.data,
                safe=False, # it's a list
                )

########################################

# TODO stub
########################################

class Notifications(generics.ListAPIView):

    serializer_class = NotificationSerializer

    permission_classes = [
            IsAuthenticated,
            ]

    def list(self, request):
        queryset = Notification.objects.filter(
                for_account = request.user.localperson,
                )

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)
