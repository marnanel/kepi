# busby_1st/views/webfinger.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

"""
Implements ".well-known/webfinger".
See [https://tools.ietf.org/html/rfc7033](RFC 7033)
for the full details.
"""

import django.views
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
import re
import json
from kepi.bowler_pub.utils import as_json, configured_url
import kepi.trilby_api.models as trilby_models

class Webfinger(django.views.View):
    """
    RFC7033 webfinger support.
    """

    def _get_body(self, request):

        try:
            user = request.GET['resource']
        except:
            logger.info('webfinger request had no username specified')
            return HttpResponse(
                    status = 400,
                    reason = 'no resource for webfinger',
                    content = 'no resource for webfinger',
                    content_type = 'text/plain',
                    )

        # Generally, user resources should be prefaced with "acct:",
        # per RFC7565. We support this, but we don't enforce it.
        user = re.sub(r'^acct:', '', user)
        logger.info('webfinger request for %s', user)

        if '@' not in user:
            logger.info('  -- no @ sign; bailing')
            return HttpResponse(
                    status = 404,
                    reason = 'absolute name required',
                    content = 'Please use the absolute form of the username.',
                    content_type = 'text/plain',
                    )

        username, hostname = user.split('@', 2)

        if hostname not in settings.ALLOWED_HOSTS:
            logger.info('  -- %s is not local; bailing',
                    hostname)
            return HttpResponse(
                    status = 404,
                    reason = 'not this server',
                    content = 'That user lives on another server.', content_type = 'text/plain',
                    )

        try:
            whoever = trilby_models.TrilbyUser.objects.get(
                    username = username,
                )
        except trilby_models.TrilbyUser.DoesNotExist:
            logger.info('  -- we don\'t have anyone called %s',
                    username)
            return HttpResponse(
                    status = 404,
                    reason = 'no such user',
                    content = 'We don\'t have a user with that name.',
                    content_type = 'text/plain',
                    )

        actor_url = configured_url('USER_LINK',
                username = username,
                )

        result = {
                "subject" : "acct:{}@{}".format(username, hostname),
                "aliases" : [
                    actor_url,
                ],

                "links":[
                    {
                    'rel': 'http://webfinger.net/rel/profile-page',
                    'type': 'text/html',
                    'href': actor_url,
                    },
                    #{
                    #'rel': 'http://schemas.google.com/g/2010#updates-from',
                    #'type': 'application/atom+xml',
                    #'href': 'FIXME', # FIXME whoever['feedURL'],
                    #},
                    {
                    'rel': 'self',
                    'type': 'application/activity+json',
                    'href': actor_url,
                    },
                    {
                    'rel': 'http://ostatus.org/schema/1.0/subscribe',
                    'template': configured_url('AUTHORIZE_FOLLOW_LINK'),
                    },
                    ]}

        logger.debug('  -- webfinger for %s was successful',
                user)

        return HttpResponse(
                status = 200,
                reason = 'Here you go',
                content = bytes(as_json(result),
                    encoding='utf-8'),
                content_type='application/jrd+json; charset=utf-8')

    def get(self, request):
        result = self._get_body(request)

        result['Access-Control-Allow-Origin'] = '*'
        return result
