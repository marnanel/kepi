# views.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
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
from .serializers import *
import kepi.trilby_api.signals as kepi_signals
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
                like.save()

            logger.info('  -- created a Like')

            kepi_signals.liked.send(sender=like)

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

        content = 'RT {}'.format(the_status.content)

        new_status = trilby_models.Status(

                # Fields which are different in a reblog:
                account = request.user.localperson,
                content = content,
                reblog_of = the_status,

                # Fields which are just copied in:
                sensitive = the_status.sensitive,
                spoiler_text = the_status.spoiler_text,
                visibility = the_status.visibility,
                language = the_status.language,
                in_reply_to = the_status.in_reply_to,
                )

        with transaction.atomic():
            new_status.save()

        logger.info('  -- created a reblog')

        kepi_signals.reblogged.send(sender=new_status)

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
                follow.save()

            logger.info('  -- follow: %s', follow)
            logger.debug('    -- offer ID: %s', offer)
            kepi_signals.followed.send(sender=follow)

            if the_person.auto_follow:
                follow_back = trilby_models.Follow(
                    follower = the_person,
                    following = request.user.localperson,
                    offer = None,
                    )

                with transaction.atomic():
                    follow_back.save()

                logger.info('  -- follow back: %s', follow_back)
                kepi_signals.followed.send(sender=follow_back)

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
            kepi_signals.unfollowed.send(sender=follow)

            with transaction.atomic():
                follow.delete()

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

class Verify_Credentials(generics.GenericAPIView):

    queryset = TrilbyUser.objects.all()

    def get(self, request, *args, **kwargs):
        serializer = UserSerializerWithSource(request.user.localperson)
        return JsonResponse(serializer.data)

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
                content = data.get('status', ''),
                sensitive = data.get('sensitive', False),
                spoiler_text = data.get('spoiler_text', ''),
                visibility = data.get('visibility', 'public'),
                language = data.get('language',
                    settings.KEPI['LANGUAGES'][0]),
                # FIXME: in_reply_to
                # FIXME: media_ids
                # FIXME: idempotency_key
                )

        status.save()

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

# TODO stub
class AccountsSearch(generics.ListAPIView):

    queryset = trilby_models.Person.objects.all()
    serializer_class = UserSerializer

    permission_classes = [
            IsAuthenticated,
            ]

########################################

# TODO stub
class Search(View):

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

########################################

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

########################################

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
