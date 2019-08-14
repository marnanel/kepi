# views/webfinger.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
Implements ".well-known/webfinger".
See [https://tools.ietf.org/html/rfc7033](RFC 7033)
for the full details.
"""

import django.views
from django.conf import settings
from django.shortcuts import render
from django_kepi.models.actor import Actor
from django.http import HttpResponse
import logging
import re
import json

logger = logging.Logger('django_kepi')

class Webfinger(django.views.View):
    """
    RFC7033 webfinger support.
    """

    def _get_body(self, request):

        try:
            user = request.GET['resource']
        except:
            return HttpResponse(
                    status = 400,
                    reason = 'no resource for webfinger',
                    content = 'no resource for webfinger',
                    content_type = 'text/plain',
                    )

        # Generally, user resources should be prefaced with "acct:",
        # per RFC7565. We support this, but we don't enforce it.
        user = re.sub(r'^acct:', '', user)

        if '@' not in user:
            return HttpResponse(
                    status = 404,
                    reason = 'absolute name required',
                    content = 'Please use the absolute form of the username.',
                    content_type = 'text/plain',
                    )

        username, hostname = user.split('@', 2)

        if hostname not in settings.ALLOWED_HOSTS:
            return HttpResponse(
                    status = 404,
                    reason = 'not this server',
                    content = 'That user lives on another server.', content_type = 'text/plain',
                    )

        try:
            whoever = Actor.objects.get(
                    remote_url = None,
                    f_preferredUsername = username,
                )
        except Actor.DoesNotExist:
            return HttpResponse(
                    status = 404,
                    reason = 'no such user',
                    content = 'We don\'t have a user with that name.',
                    content_type = 'text/plain',
                    )

        actor_url = settings.KEPI['USER_URL_FORMAT'] % {
                'username': username,
                'hostname': hostname,
                }

        result = {
                "subject" : "acct:{}@{}".format(username, hostname),
                "aliases" : [
                    actor_url,
                ],

                "links":[
                    {
                        "rel"  : "self",
                        "type" : "application/activity+json",
                        "href" : actor_url,
                    },
                    ]}

        return HttpResponse(
                status = 200,
                reason = 'Here you go',
                content = bytes(json.dumps(result, indent=2),
                    encoding='utf-8'),
                content_type='application/jrd+json; charset=utf-8')

    def get(self, request):
        result = self._get_body(request)

        result['Access-Control-Allow-Origin'] = '*'
        return result


