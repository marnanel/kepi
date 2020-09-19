# tophat_ui/urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.urls import path, re_path
import kepi.tophat_ui.views as tophat_views

urlpatterns = [
        path('', tophat_views.RootPageView.as_view()),
        ]
