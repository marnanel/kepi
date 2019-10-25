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
from .models import TrilbyUser
from .serializers import *
from rest_framework import generics, response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
import logging
import chapeau.kepi.models as kepi_models
import json
import re

logger = logging.Logger(name='chapeau')

###########################

class Instance(View):

    def get(self, request, *args, **kwargs):

        result = {
            'uri': 'http://127.0.0.1',
            'title': settings.KEPI['INSTANCE_NAME'],
            'description': settings.KEPI['INSTANCE_DESCRIPTION'],
            'email': settings.KEPI['CONTACT_EMAIL'],
            'version': 'un_0.0.1',
            'urls': {},
            'languages': settings.KEPI['LANGUAGES'],
            'contact_account': settings.KEPI['CONTACT_ACCOUNT'],
            }

        return JsonResponse(result)

###########################

def fix_oauth2_redirects():
    """
    Called from chapeau.chapeau.urls to fix a silly oversight
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
        serializer = UserSerializerWithSource(request.user)
        return JsonResponse(serializer.data)

class Statuses(generics.ListCreateAPIView):

    queryset = kepi_models.AcCreate.objects.all()

    def get(self, request, *args, **kwargs):

        queryset = self.get_queryset()

        if 'id' in kwargs:
            number = '/'+kwargs['id']
            logger.info('Looking up status numbered %s for %s',
                    number, request.user)

            create = queryset.get(id=number)
            serializer = StatusSerializer(create['object__obj'])
        else:
            logger.info('Looking up all visible statuses for %s',
                   request.user)
            # ... FIXME
            serializer = StatusSerializer(queryset)

        return JsonResponse(serializer.data)

class AbstractTimeline(generics.ListAPIView):

    serializer_class = StatusSerializer
    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self, request):
        raise NotImplementedError("cannot query abstract timeline")

    def list(self, request):
        queryset = self.get_queryset(request)
        serializer = self.serializer_class(queryset,
                many = True,
                context = {
                    'request': request,
                    })
        return Response(serializer.data)

class PublicTimeline(AbstractTimeline):

    permission_classes = ()

    def get_queryset(self, request):
        return AcItem.objects.filter(visibility='public')

class HomeTimeline(AbstractTimeline):

    permission_classes = [
            IsAuthenticated,
            ]

    def get_queryset(self, request):

        return kepi_models.Collection.get(
                user = request.user.actor,
                collection = 'inbox').members

########################################

class UserFeed(View):

    permission_classes = ()

    def get(self, request, username, *args, **kwargs):

        user = get_object_or_404(kepi_models.AcActor,
                id = '@'+username,
                )

        statuses = [x.member for x in kepi_models.Collection.get(
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

class UserActivityView(View):

    permission_classes = ()

    def objectDetails(self, *args, **kwargs):

        username = kwargs['username']
        user = get_object_or_404(TrilbyUser, username=username)

        return {
                "followers": user.followersURL(),
                "outbox": user.outboxURL(),
                "following": user.followingURL(),
                "featured": user.featuredURL(),
                "attachment": [],
                "endpoints": {
                    "sharedInbox": settings.KEPI.get('SHARED_INBOX_URL'),
                    },
                "tag": [],
                "inbox": user.inboxURL(),

                # XXX this dict should be coming from the image object
                "image": {
                    "type": "Image",
                    # XXX enormous hack until we get media working properly
                    "url": "https://{}/static/defaults/header.jpg".format(settings.KEPI['LOCAL_OBJECT_HOSTNAME']),
                    #"url": user.header,
                    "mediaType": "image/jpeg",
                    },
                "icon": {
                    "type": "Image",
                    # XXX enormous hack until we get media working properly
                    "url": "https://{}/static/defaults/avatar_1.jpg".format(settings.KEPI['LOCAL_OBJECT_HOSTNAME']),
                    #"url": user.avatar,
                    "mediaType": "image/jpeg",
                    },
                "preferredUsername": user.username,
                "type": "Person",
                "id": user.activityURL(),
                "summary": user.note,
                "id": user.activityURL(),
                "@context": UN_CHAPEAU["ATSIGN_CONTEXT"],
                "publicKey": {
                    "id": '{}#main-key'.format(user.activityURL(),),
                    "owner": user.activityURL(),
                    "publicKeyPem": user.public_key,
                    },
                "name": user.username,
                "manuallyApprovesFollowers": user.default_sensitive,
                }

########################################

class ActivityFollowingView(View):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = settings.KEPI.get('USER_URLS',
                username = kwargs['username']
                )
        return super().get_collection_items(*args, **kwargs)

    def _stringify_object(self, obj):
        return obj.following.url

class ActivityFollowersView(View):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = settings.KEPI.get('USER_URLS',
                username = kwargs['username']
                )
        return super().get_collection_items(*args, **kwargs)

    def _stringify_object(self, obj):
        return obj.follower.url

class ActivityOutboxView(View):

    def get_collection_items(self, *args, **kwargs):
        user = get_object_or_404(TrilbyUser, username=kwargs['username'])
        return Status.objects.filter(posted_by=user)

    def _stringify_object(self, obj):
        # XXX We'll do this properly soon.
        # It should have views particular to each kind of Status,
        # and an integration with the Activities in kepi.
        return {
         "object" : {
            "atomUri" : obj.atomURL(),
            "id" : obj.activityURL(),
            "sensitive" : obj.is_sensitive(),
            "attachment" : [],
            "contentMap" : {
               "en" : obj.content,
            },
            "url" : obj.url(),
            "content" : obj.content,
            "inReplyTo" : None,
            "published" : iso_date(obj.created_at),
            "inReplyToAtomUri" : None,
            "to" : [
               "https://www.w3.org/ns/activitystreams#Public"
            ],
            "type" : "Note",
            "cc" : [
               obj.posted_by.followersURL(),
            ],
            "attributedTo" : obj.posted_by.activityURL(),
            "tag" : [],
            "conversation" : obj.conversation(),
         },
         "published" : iso_date(obj.created_at),
         "id" : obj.activityURL(),
         "type" : "Create",
         "to" : [
            "https://www.w3.org/ns/activitystreams#Public"
         ],
         "actor" : obj.posted_by.activityURL(),
         "cc" : [
             obj.posted_by.followersURL(),
         ]
      }

class FeaturedCollectionView(View):
    # FIXME
    def get_collection_items(self, *args, **kwargs):
        return Status.objects.none()

class Notifications(View):
    # FIXME
    def get(self, request, *args, **kwargs):
        return JsonResponse([],
                safe=False)

class Filters(View):
    # FIXME
    def get(self, request, *args, **kwargs):
        return JsonResponse([],
                safe=False)
