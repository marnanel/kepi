# tophat_ui/urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.urls import path, re_path
import django.contrib.auth.views
import kepi.tophat_ui.views as tophat_views
import kepi.tophat_ui.forms as tophat_forms

urlpatterns = [
        path('', tophat_views.RootPage.as_view()),

        path('login/', django.contrib.auth.views.LoginView.as_view(
            extra_context = {
                'next': '/',
                },
            )),

        ]
