from django.urls import path, re_path
from django_kepi.views import *

urlpatterns = [
        re_path('^(?P<id>[0-9a-z]{8})$', ThingView.as_view()),
        path('users', AllUsersView.as_view()),
        path('users/<str:name>', ActorView.as_view()),
        path('users/<str:name>/inbox', InboxView.as_view()),
        path('users/<str:name>/followers', FollowersView.as_view()),
        path('users/<str:name>/following', FollowingView.as_view()),
        path('sharedInbox', InboxView.as_view()),
        ]

