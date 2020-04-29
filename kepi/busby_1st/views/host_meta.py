# views/host_meta.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
Implements ".well-known/host-meta".
See [https://tools.ietf.org/html/rfc6415](RFC 6415)
for the full details.
"""

import django.views
from django.shortcuts import render
import logging

logger = logging.Logger('kepi')

class HostMeta(django.views.View):

    def get(self, request):

        logger.info('Returning host-meta.xml')

        context = {
                'hostname': request.get_host(),
            }

        result = render(
                request=request,
                template_name='host-meta.xml',
                context=context,
                content_type='application/xrd+xml',
                )

        return result

