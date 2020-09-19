# urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These are URL patterns, to include from your app's urls.py.
"""

from django.urls import path, re_path
import kepi.bowler_pub.views as bowler_pub_views

urlpatterns = [
        path('users', bowler_pub_views.AllUsersView.as_view()),
        path('users/<str:username>', bowler_pub_views.PersonView.as_view()),
        path('users/<str:username>/inbox', bowler_pub_views.InboxView.as_view()),
        path('users/<str:username>/outbox', bowler_pub_views.OutboxView.as_view()),
        path('users/<str:username>/followers', bowler_pub_views.FollowersView.as_view()),
        path('users/<str:username>/following', bowler_pub_views.FollowingView.as_view()),
        path('users/<str:username>/<int:status>', bowler_pub_views.StatusView.as_view()),
        path('sharedInbox', bowler_pub_views.InboxView.as_view()),
        ]
