# views.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.views import View
from django.shortcuts import render

class RootPageView(View):

    def get(self, request, *args, **kwargs):

        logger.info("Serving root page")

        result = render(
                request=request,
                template_name='root-page.html',
                content_type='text/html',
                )

        return result
