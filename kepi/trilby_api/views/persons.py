# trilby_api/views/persons.py
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

class UpdateCredentials(generics.GenericAPIView):

    def patch(self, request, *args, **kwargs):

        if request.user is None:
            logger.debug('  -- user not logged in')
            return error_response(401, 'Not logged in')

        who = request.user.localperson

        # The Mastodon spec doesn't say what to do
        # if the user submits field names which don't
        # exist!

        unknown_fields = []

        # FIXME: the data in "v" needs cleaning.

        logger.info('-- updating user: %s', who)

        for f,v in request.data.items():

            logger.info('  -- setting %s = %s', f, v)

            if f=='discoverable':
                raise Http404("discoverable is not yet supported")
            elif f=='bot':
                who.bot = v
            elif f=='display_name':
                who.display_name = v
            elif f=='note':
                who.note = v
            elif f=='avatar':
                raise Http404("images are not yet supported")
            elif f=='header':
                raise Http404("images are not yet supported")
            elif f=='locked':
                who.locked = v
            elif f=='source[privacy]':
                who.default_visibility = v
            elif f=='source[sensitive]':
                who.default_sensitive = v
            elif f=='source[language]':
                who.language = v
            elif f=='fields_attributes':
                raise Http404("fields are not yet supported")
            else:
                logger.info('    -- field does not exist')
                unknown_fields.append(f)

        if unknown_fields:
            logger.info('  -- aborting because of unknown fields')
            raise Http404(f"some fields do not exist: {unknown_fields}")

        who.save()
        logger.info('  -- done.')

        serializer = UserSerializerWithSource(
                who,
                context = {
                    'request': request,
                    },
                )

        return JsonResponse(
                serializer.data,
                status = 200,
                reason = 'Done',
                )

###########################

class VerifyCredentials(generics.GenericAPIView):

    queryset = TrilbyUser.objects.all()

    def get(self, request, *args, **kwargs):
        serializer = UserSerializerWithSource(request.user.localperson)
        return JsonResponse(serializer.data)

###########################

class User(generics.GenericAPIView):

    queryset = trilby_models.Person.objects.all()

    def get(self, request, *args, **kwargs):
        try:
            whoever = get_object_or_404(
                    self.get_queryset(),
                    id = int(kwargs['user']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        serializer = UserSerializer(whoever)
        return JsonResponse(serializer.data)

#######################################

class Followers_or_Following(generics.GenericAPIView):
    serializer_class = UserSerializer
    queryset = trilby_models.Person.objects.all()

    def get(self, request, *args, **kwargs):

        params = request.data

        if request.user.localperson is None:
            logger.debug('  -- user not logged in')
            return error_response(401, 'Not logged in')

        try:
            the_person = get_object_or_404(
                    self.get_queryset(),
                    id = int(kwargs['user']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        queryset = self._get_list_for(the_person)

        if 'max_id' in params:
            queryset = queryset.filter(
                    id__le = params['max_id'],
                    )

        if 'since_id' in params:
            queryset = queryset.filter(
                    id__gt = params['since_id'],
                    )

        if 'limit' in params:
            queryset = queryset[:params['limit']]

        serializer = UserSerializer(
                queryset,
                many = True,
                context = {
                    'request': request,
                    },
                )

        return JsonResponse(
                serializer.data,
                safe = False, # it's a list
                status = 200,
                reason = 'Done',
                )

class Followers(Followers_or_Following):
    def _get_list_for(self, the_person):
        return the_person.followers

class Following(Followers_or_Following):
    def _get_list_for(self, the_person):
        return the_person.following
    
###########################

class UpdateCredentials(generics.GenericAPIView):

    def patch(self, request, *args, **kwargs):

        if request.user is None:
            logger.debug('  -- user not logged in')
            return error_response(401, 'Not logged in')

        who = request.user.localperson

        # The Mastodon spec doesn't say what to do
        # if the user submits field names which don't
        # exist!

        unknown_fields = []

        # FIXME: the data in "v" needs cleaning.

        logger.info('-- updating user: %s', who)

        for f,v in request.data.items():

            logger.info('  -- setting %s = %s', f, v)

            if f=='discoverable':
                raise Http404("discoverable is not yet supported")
            elif f=='bot':
                who.bot = v
            elif f=='display_name':
                who.display_name = v
            elif f=='note':
                who.note = v
            elif f=='avatar':
                raise Http404("images are not yet supported")
            elif f=='header':
                raise Http404("images are not yet supported")
            elif f=='locked':
                who.locked = v
            elif f=='source[privacy]':
                who.default_visibility = v
            elif f=='source[sensitive]':
                who.default_sensitive = v
            elif f=='source[language]':
                who.language = v
            elif f=='fields_attributes':
                raise Http404("fields are not yet supported")
            else:
                logger.info('    -- field does not exist')
                unknown_fields.append(f)

        if unknown_fields:
            logger.info('  -- aborting because of unknown fields')
            raise Http404(f"some fields do not exist: {unknown_fields}")

        who.save()
        logger.info('  -- done.')

        serializer = UserSerializerWithSource(
                who,
                context = {
                    'request': request,
                    },
                )

        return JsonResponse(
                serializer.data,
                status = 200,
                reason = 'Done',
                )
