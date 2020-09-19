# parsers.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
django-rest-framework provides a JSON parser, which
does what we need for parsing ActivityPub. However,
it baulks at the ActivityPub MIME type. So we have a
subclass here with only the accepted MIME type changed.
"""

from rest_framework.parsers import JSONParser

class ActivityParser(JSONParser):
    """
    django-rest-framework parser for application/activity+json.
    """
    media_type = "application/activity+json"
