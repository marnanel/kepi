# busby_1st/urls.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.urls import path, re_path
import kepi.busby_1st.views as busby_views

urlpatterns = [
        path('.well-known/host-meta', busby_views.HostMeta.as_view()),
        path('.well-known/webfinger', busby_views.Webfinger.as_view()),
        path('.well-known/nodeinfo', busby_views.NodeinfoPart1.as_view()),
        path('nodeinfo.json', busby_views.NodeinfoPart2.as_view()),
        ]
