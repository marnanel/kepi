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
        if result.func.__name__ not in which_views:
            result = None

    return result
