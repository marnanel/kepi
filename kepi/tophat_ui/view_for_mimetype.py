# view_for_mimetype.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.
#
# This might work better as a standalone module,
# separate from kepi?

import logging
logger = logging.getLogger(name='kepi')

from kepi.tophat_ui.parse_accept import parse_accept_header
from django.http import HttpResponse

def view_for_mimetype(
        views,
        default = None,
        ):
    """
    """

    def _view_for_mimetype_inner(
            request,
            ):

        accept_header = request.headers.get('Accept', '')
        accept_parsed = parse_accept_header(accept_header)

        logger.debug("Accept=%s -> %s", accept_header, accept_parsed)

        for want_type, want_subtype, params, q in accept_parsed:

            for have_type, have_subtype, view in views:

                if want_type != have_type:
                    continue

                if want_subtype not in (have_subtype, '*'):
                    continue

                logger.debug('  -- found %s/%s: %s',
                        have_type, have_subtype, view)

                result = view(request)
                return result

        if default is not None:
            logger.debug('  -- using default: %s',
                    have_type, have_subtype, view)

            result = default(request)
            return result
        else:
            logger.debug('  -- none found; 406')

            # return 406 Not Acceptable
            return HttpResponse(status=406)

    return _view_for_mimetype_inner 
