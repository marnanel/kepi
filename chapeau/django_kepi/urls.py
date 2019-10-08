# urls.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These are URL patterns, to include from your app's urls.py.
"""

from django.urls import path, re_path
import django_kepi.views

urlpatterns = [
        re_path('^(?P<id>[0-9a-z]{8})$', django_kepi.views.ThingView.as_view()),
        path('users', django_kepi.views.AllUsersView.as_view()),
        path('users/<str:username>', django_kepi.views.ActorView.as_view()),
        path('users/<str:username>/inbox', django_kepi.views.InboxView.as_view(),
            { 'listname': 'inbox', } ),
        path('users/<str:username>/outbox', django_kepi.views.OutboxView.as_view(),
            { 'listname': 'outbox', } ),
        path('users/<str:username>/followers', django_kepi.views.FollowersView.as_view()),
        path('users/<str:username>/following', django_kepi.views.FollowingView.as_view()),
        path('sharedInbox', django_kepi.views.InboxView.as_view()),

        # XXX We might want to split out the patterns that HAVE to be
        # at the root.

        path('.well-known/host-meta', django_kepi.views.HostMeta.as_view()),
        path('.well-known/webfinger', django_kepi.views.Webfinger.as_view()),
        path('.well-known/nodeinfo', django_kepi.views.NodeinfoPart1.as_view()),
        path('nodeinfo.json', django_kepi.views.NodeinfoPart2.as_view()),
        ]

