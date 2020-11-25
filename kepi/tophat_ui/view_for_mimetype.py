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
    Returns a Django view function which can route requests
    to other view functions based on the incoming Accept header.

    Params:
      views - a list of (type, subtype, view) triplets
        e.g. ('text', 'html', HelloWorldView)

      default - the default to return if the Accept header
        can't otherwise be satisfied.

    If you don't give a default, the view function returns
    a new HttpResponse with status_code==406, i.e. "Not Acceptable".
    See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/406

    As a special case, if request is None, returns the list of views.
    A default value will be at the end, with type and subtype set to None.
    """

    def _view_for_mimetype_inner(
            request,
            *args, **kwargs,
            ):

        if request is None:
            result = views.copy()

            if default is not None:
                result.append((None, None, default))

            return result

        accept_header = request.headers.get('Accept', '')
        accept_parsed = parse_accept_header(accept_header)

        logger.debug("Accept=%s -> %s", accept_header, accept_parsed)
        logger.debug("Views: %s", views)

        for want_type, want_subtype, params, q in accept_parsed:

            for have_type, have_subtype, view in views:

                if want_type != have_type:
                    continue

                if want_subtype not in (have_subtype, '*'):
                    continue

                logger.debug('  -- found %s/%s: %s',
                        have_type, have_subtype, view)

                result = view(request,
                        *args, **kwargs,
                        )
                return result

        if default is not None:
            logger.debug('  -- using default: %s',
                    view)

            result = default(request,
                        *args, **kwargs,
                        )
            return result
        else:
            logger.debug('  -- none found; 406')

            # return 406 Not Acceptable
            return HttpResponse(status=406)

    return _view_for_mimetype_inner 
