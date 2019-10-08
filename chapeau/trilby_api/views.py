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
from .models import Status, TrilbyUser, Visibility, iso_date, MessageCapturer
from .serializers import *
from rest_framework import generics, response
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
import django_kepi.models as kepi_models
import json
import re

###########################

class Instance(View):

    def get(self, request, *args, **kwargs):

        result = {
            'uri': 'http://127.0.0.1',
            'title': settings.KEPI['INSTANCE_NAME'],
            'description': settings.KEPI['INSTANCE_DESCRIPTION'],
            'email': settings.KEPI['CONTACT_EMAIL'],
            'version': 'un_chapeau 0.0.1',
            'urls': {},
            'languages': settings.KEPI['LANGUAGES'],
            'contact_account': settings.KEPI['CONTACT_ACCOUNT'],
            }

        return JsonResponse(result)

###########################

class Apps(View):

    def post(self, request, *args, **kwargs):

        new_app = Application(
            name = request.POST['client_name'],
            redirect_uris = request.POST['redirect_uris'],
            client_type = 'confidential', # ?
            authorization_grant_type = 'password',
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

    def get(self, request):
        serializer = UserSerializerWithSource(request.user)
        return Response(serializer.data)

class Statuses(generics.ListCreateAPIView):

    queryset = Status.objects.all()
    serializer_class = StatusSerializer

class AbstractTimeline(generics.ListAPIView):

    serializer_class = StatusSerializer
    permission_classes = ()

    def get_queryset(self):
        raise RuntimeError("cannot query abstract timeline")

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset,
                many = True,
                context = {
                    'request': request,
                    })
        return Response(serializer.data)

class PublicTimeline(AbstractTimeline):

    permission_classes = ()

    def get_queryset(self):
        return Status.objects.filter(visibility=Visibility('public').name)

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

class FIXMEview(View):
    pass

########################################

class UserActivityView(FIXMEview):

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

class ActivityFollowingView(FIXMEview):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = settings.KEPI.get('USER_URLS',
                username = kwargs['username']
                )
        return super().get_collection_items(*args, **kwargs)

    def _stringify_object(self, obj):
        return obj.following.url

class ActivityFollowersView(FIXMEview):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = settings.KEPI.get('USER_URLS',
                username = kwargs['username']
                )
        return super().get_collection_items(*args, **kwargs)

    def _stringify_object(self, obj):
        return obj.follower.url

class ActivityOutboxView(FIXMEview):

    def get_collection_items(self, *args, **kwargs):
        user = get_object_or_404(TrilbyUser, username=kwargs['username'])
        return Status.objects.filter(posted_by=user)

    def _stringify_object(self, obj):
        # XXX We'll do this properly soon.
        # It should have views particular to each kind of Status,
        # and an integration with the Activities in django_kepi.
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

class FeaturedCollectionView(FIXMEview):

    # I have no idea what this is, and it doesn't seem to be in the specs.
    # But Mastodon expects it, so...

    def get_collection_items(self, *args, **kwargs):
        return Status.objects.none()

########################################

class Webfinger(generics.GenericAPIView):
    """
    RFC7033 webfinger support.
    """

    serializer_class = WebfingerSerializer
    permission_classes = ()
    renderer_classes = (JSONRenderer, )

    def _get_body(self, request):

        try:
            user = request.GET['resource']
        except MultiValueDictKeyError:
            return HttpResponse(
                    status = 400,
                    reason = 'no resource for webfinger',
                    content = 'no resource for webfinger',
                    content_type = 'text/plain',
                    )

        # Generally, user resources should be prefaced with "acct:",
        # per RFC7565. We support this, but we don't enforce it.
        user = re.sub(r'^acct:', '', user)

        if '@' not in user:
            return HttpResponse(
                    status = 404,
                    reason = 'absolute name required',
                    content = 'Please use the absolute form of the username.',
                    content_type = 'text/plain',
                    )

        username, hostname = user.split('@', 2)

        if hostname!=settings.KEPI['LOCAL_OBJECT_HOSTNAME']:
            return HttpResponse(
                    status = 404,
                    reason = 'not this server',
                    content = 'That user lives on another server.',
                    content_type = 'text/plain',
                    )

        try:
            queryset = TrilbyUser.objects.get(username=username)
        except TrilbyUser.DoesNotExist:
            return HttpResponse(
                    status = 404,
                    reason = 'no such user',
                    content = 'We don\'t have a user with that name.',
                    content_type = 'text/plain',
                    )

        serializer = self.serializer_class(queryset)
        return Response(serializer.data,
                content_type='application/jrd+json; charset=utf-8')

    def get(self, request):
        result = self._get_body(request)

        result['Access-Control-Allow-Origin'] = '*'
        return result

########################################

class HostMeta(View):

    permission_classes = ()

    def get(self, request):

        context = {
                'server_name': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
            }

        result = render(
                request=request,
                template_name='host-meta.xml',
                context=context,
                content_type='application/jrd+xml',
                )

        return result

########################################

class MessageCapturingView(View):

    def post(self, request, *args, **kwargs):

        capture = MessageCapturer(
                box = request.path,
                content = str(request.body, encoding='UTF-8'),
                headers = str(request.META),
                )
        capture.save()

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )


