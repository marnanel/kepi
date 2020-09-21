# parsers.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
A custom django-rest-framework parser for ActivityPub.
"""

import codecs
from django.conf import settings
from rest_framework.parsers import BaseParser

class ActivityParser(BaseParser):
    """
    django-rest-framework parser for application/activity+json.
    """
    media_type = "application/activity+json"

    def parse(self, stream, media_type=None, parser_context=None):

        """
        Traditionally, we'd be parsing the JSON here. But despite
        the name, we don't parse the incoming stream here at all.
        This is because validate() needs to know the exact content
        in order to test the signature. So we just pass it back
        as a bytestring.
        """

        result = stream.read()

        return result
