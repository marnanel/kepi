# urls.py
#
# Part of  an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These are URL patterns, to include from your app's urls.py.
"""

from django.urls import path, re_path
import chapeau.kepi.views as kepi_views

urlpatterns = [
        re_path('^(?P<id>[0-9a-z]{8})$', kepi_views.ThingView.as_view()),
        path('users', kepi_views.AllUsersView.as_view()),
        path('users/<str:username>', kepi_views.ActorView.as_view()),
        path('users/<str:username>/inbox', kepi_views.InboxView.as_view(),
            { 'listname': 'inbox', } ),
        path('users/<str:username>/outbox', kepi_views.OutboxView.as_view(),
            { 'listname': 'outbox', } ),
        path('users/<str:username>/followers', kepi_views.FollowersView.as_view()),
        path('users/<str:username>/following', kepi_views.FollowingView.as_view()),
        path('sharedInbox', kepi_views.InboxView.as_view()),

        # XXX We might want to split out the patterns that HAVE to be
        # at the root.

        path('.well-known/host-meta', kepi_views.HostMeta.as_view()),
        path('.well-known/webfinger', kepi_views.Webfinger.as_view()),
        path('.well-known/nodeinfo', kepi_views.NodeinfoPart1.as_view()),
        path('nodeinfo.json', kepi_views.NodeinfoPart2.as_view()),
        ]

