# views.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.views import View
from django.shortcuts import render
from django.conf import settings

import kepi.trilby_api.models as trilby_models

class RootPage(View):

    def get(self, request, *args, **kwargs):

        logger.info("Serving root page")

        result = render(
                request=request,
                template_name='root-page.html',
                context = {
                    'title': settings.KEPI['INSTANCE_NAME'],
                    'subtitle': settings.KEPI['INSTANCE_DESCRIPTION'],
                    'blurb': settings.KEPI['INSTANCE_BLURB'],
                    },
                )

        return result

class UserPage(View):

    def get(self, request,
            username,
            *args, **kwargs):

        logger.info("Serving user page for %s",
                username,
                )

        user = trilby_models.LocalPerson.objects.get(
                local_user__username = username,
                )

        result = render(
                request=request,
                template_name='user-page.html',
                context = {
                    'title': user.username,
                    'subtitle': user.display_name,
                    'bio': user.note,
                    },
                )

        return result

class StatusPage(View):

    def get(self, request,
            username,
            status,
            *args, **kwargs):

        logger.info("Serving status page for %s/%s",
                username,
                status,
                )

        stat = trilby_models.Status.objects.get(
                remote_url = None, # we can only serve local statuses
                id = status,
                )

        user = stat.account

        if not user.is_local:
            logger.info("  -- not posted by a local user; 404")
            raise Http404()

        if user.username != username:
            logger.info("  -- which was actually posted by %s; 404",
                    user.username)
            raise Http404()

        result = render(
                request=request,
                template_name='status-page.html',
                context = {
                    'title': user.username,
                    'subtitle': '',
                    'status': stat,
                    },
                )

        return result
