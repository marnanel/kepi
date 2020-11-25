# utils.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

VISIBILITY_PUBLIC = 'A'
VISIBILITY_UNLISTED = 'U'
VISIBILITY_PRIVATE = 'X'
VISIBILITY_DIRECT = 'D'

VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, 'public'),
        (VISIBILITY_UNLISTED, 'unlisted'),
        (VISIBILITY_PRIVATE, 'private'),
        (VISIBILITY_DIRECT, 'direct'),
        ]

VISIBILITY_HELP_TEXT = "Public (A): visible to anyone.\n"+\
        "Unlisted (U): visible to anyone, but "+\
        "doesn't appear in timelines.\n"+\
        "Private (X): only visible to followers.\n"+\
        "Direct (D): visible to nobody except tagged people.\n"+\
        "\n"+\
        "Additionally, a person tagged in a status can\n"+\
        "always view that status."

def find_local_view(url,
        which_views = None):

    """
    If the URL refers to a view on the current server,
    returns a django.utils.ResolverMatch for that view,
    with keywords according to the URL.

    If the URL is malformed, or doesn't refer to the
    current server, or doesn't refer to a view on the
    current server, returns None.

    Optionally, you can specify a list of strings in
    which_views. If a result is found, and the name of
    the view function is a member of that list, it
    will be returned in the ordinary way. Otherwise,
    this function will return None.
    """

    from urllib.parse import urlparse
    from django.conf import settings
    from django.urls import resolve
    from django.urls.exceptions import Resolver404

    parsed_url = urlparse(url)

    if parsed_url.hostname not in settings.ALLOWED_HOSTS:
        # not an address on this server
        return None

    try:
        result = resolve(parsed_url.path)
    except Resolver404:
        result = None

    if result is not None and which_views is not None:

        name = result.func.__name__

        if name=='_view_for_mimetype_inner':

            # Special case if this is view_for_mimetype.
            # The actual views behind VFM can be accessed
            # by passing None as a parameter.

            have_views = set([
                    x[2].__name__ for x in result.func(None)
                    ])

            logger.debug("Checking whether the views %s match %s",
                    have_views, which_views)

            if not have_views.intersection(set(which_views)):
                logger.debug("  -- no")
                result = None

        else:

            # it's an ordinary view function, so the answer
            # is much easier

            logger.debug("Checking whether the view %s matches %s",
                    name, which_views)

            if name not in which_views:
                logger.debug("  -- no")
                result = None

    return result
