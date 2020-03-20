from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import HttpResponse, JsonResponse
from oauth2_provider.models import Application
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.datastructures import MultiValueDictKeyError
from django.core.exceptions import SuspiciousOperation
from django.conf import settings
from .models import TrilbyUser, Notification, Status
from .serializers import *
from rest_framework import generics, response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
import logging
import kepi.bowler_pub.models as bowler_pub_models
import json
import re

logger = logging.Logger(name='kepi')

###########################

# Decorator
def id_field_int_to_hex(func):
    def wrapper(*args, **kwargs):
        if 'id' in kwargs:
            as_hex = '%08x' % (int(kwargs['id']),)
            logger.debug('Converting decimal id=%s into hex id=%s',
                    kwargs['id'], as_hex)
            kwargs['id'] = as_hex

        return func(*args, **kwargs)

    return wrapper

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
    queryset = AcItem.objects.all()

    def _do_something_with(self, the_status, request):
        raise NotImplementedError()

    def post(self, request, *args, **kwargs):

        try:
            the_status = get_object_or_404(
                    self.get_queryset(),
                    serial = int(kwargs['id']),
                    )
        except ValueError:
            return error_response(404, 'Non-decimal ID')

        if request.user is None:
            logger.debug('  -- user not logged in')
            return error_response(401, 'Not logged in')

        self._do_something_with(the_status, request)

        serializer = StatusSerializer(
                the_status,
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
        existing = bowler_pub_models.AcLike.objects.filter(
            f_actor = request.user.person.acct,
            f_object = the_status.id,
            ).exists()

        if existing:
            logger.info('  -- not creating a Like; it already exists')
        else:
            logger.info('  -- creating a Like')
            bowler_pub_create(value={
                'type': 'Like',
                'actor': request.user.person.id,
                'object': the_status.id,
                })

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
        serializer = UserSerializerWithSource(request.user.person)
        return JsonResponse(serializer.data)

class User(generics.GenericAPIView):

    queryset = AcActor.objects.all()

    def get(self, request, *args, **kwargs):
        whoever = get_object_or_404(
                self.get_queryset(),
                id='@'+kwargs['name'],
                )

        serializer = UserSerializer(whoever)
        return JsonResponse(serializer.data)

class Statuses(generics.ListCreateAPIView,
        generics.CreateAPIView,
        generics.DestroyAPIView,
        ):

    queryset = bowler_pub_models.AcItem.objects.filter_local_only()
    serializer_class = StatusSerializer

    @id_field_int_to_hex
    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        if 'id' in kwargs:
            number = '/'+kwargs['id']
            logger.info('Looking up status numbered %s, for %s',
                    number, request.user)

            activity = queryset.get(id=number)
            serializer = StatusSerializer(
                    activity,
                    partial = True,
                    context = {
                        'request': request,
                        },
                    )
        else:
            logger.info('Looking up all visible statuses, for %s',
                   request.user)

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

        status = Status(
                account = request.user.person,
                content = data.get('status'),
                sensitive = data.get('sensitive', False),
                spoiler_text = data.get('spoiler_text', ''),
                visibility = data.get('visibility', 'public'),
                language = data.get('language',
                    settings.KEPI['LANGUAGES'][0]),
                # FIXME: in_reply_to_id
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
                status = 201, # Created
                reason = 'Hot off the press',
                )

class StatusContext(generics.ListCreateAPIView):

    queryset = bowler_pub_models.AcItem.objects.all()

    @id_field_int_to_hex
    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        number = '/'+kwargs['id']
        status = queryset.get(id=number)
        serializer = StatusContextSerializer(status)

        return JsonResponse(serializer.data)

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

        result = []

        timeline = bowler_pub_models.AcItem.objects.all()

        for item in timeline:

            if item.visibility=='public':
                result.append(item)

            if len(result)>=PUBLIC_TIMELINE_SLICE_LENGTH:
                break

        return result

class HomeTimeline(AbstractTimeline):

    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self, request):

        result = []

        inbox = bowler_pub_models.Collection.get(
                user = request.user.person,
                collection = 'inbox').members

        for item in inbox:
            if item.f_type in [
                    'Create',
                    ]:
                product = item['object__obj']

                if product is not None:
                    result.append(product)

        return result

########################################

# TODO stub
class AccountsSearch(generics.ListAPIView):

    queryset = AcActor.objects.all()
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

        user = get_object_or_404(bowler_pub_models.AcActor,
                id = '@'+username,
                )

        statuses = [x.member for x in bowler_pub_models.Collection.get(
                username+'/outbox',
                ).contents]

        context = {
                'self': request.build_absolute_uri(),
                'user': user,
                'statuses': statuses,
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
                        username = user.id[1:],
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
                for_account = request.user,
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

class Followers(View):
    # FIXME
    def get(self, request, *args, **kwargs):
        return JsonResponse([],
                safe=False)

class Following(View):
    # FIXME
    def get(self, request, *args, **kwargs):
        return JsonResponse([],
                safe=False)
