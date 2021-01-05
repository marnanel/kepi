# tophat_ui/urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.urls import path, re_path
import django.contrib.auth.views
import kepi.tophat_ui.views as tophat_views
import kepi.bowler_pub.views as bowler_views
from kepi.tophat_ui.view_for_mimetype import view_for_mimetype

urlpatterns = [
        path('', tophat_views.RootPage.as_view()),

        path('users/<str:username>',
             view_for_mimetype(
                 [
                     ('application', 'activity+json',
                     bowler_views.PersonView.as_view()),
                     ],
                 default = tophat_views.UserPage.as_view(),
                 )),

        path('users/<str:username>/<int:status>',
             view_for_mimetype(
                 [
                     ('application', 'activity+json',
                     bowler_views.StatusView.as_view()),
                     ],
                 default = tophat_views.StatusPage.as_view(),
                 )),

        ]
