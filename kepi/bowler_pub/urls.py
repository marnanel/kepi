# urls.py
#
# Part of  an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These are URL patterns, to include from your app's urls.py.
"""

from django.urls import path, re_path
import kepi.bowler_pub.views as bowler_pub_views

urlpatterns = [
        re_path('^(?P<id>[0-9a-z]{8})$', bowler_pub_views.ThingView.as_view()),
        path('users', bowler_pub_views.AllUsersView.as_view()),
        path('users/<str:username>', bowler_pub_views.ActorView.as_view()),
        path('users/<str:username>/inbox', bowler_pub_views.InboxView.as_view(),
            { 'listname': 'inbox', } ),
        path('users/<str:username>/outbox', bowler_pub_views.OutboxView.as_view(),
            { 'listname': 'outbox', } ),
        path('users/<str:username>/followers', bowler_pub_views.FollowersView.as_view()),
        path('users/<str:username>/following', bowler_pub_views.FollowingView.as_view()),
        path('sharedInbox', bowler_pub_views.InboxView.as_view()),

        # XXX We might want to split out the patterns that HAVE to be
        # at the root.

        path('.well-known/host-meta', bowler_pub_views.HostMeta.as_view()),
        path('.well-known/webfinger', bowler_pub_views.Webfinger.as_view()),
        path('.well-known/nodeinfo', bowler_pub_views.NodeinfoPart1.as_view()),
        path('nodeinfo.json', bowler_pub_views.NodeinfoPart2.as_view()),
        ]

