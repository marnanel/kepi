# activityresponse.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from django.http import HttpResponse

import logging
logger = logging.getLogger(name="kepi")

class ActivityResponse(HttpResponse):

    """
    This is a workaround.

    Methods in ordinary Django views can return anything at all,
    but d-r-f adds an assertion that they return HttpResponse objects.
    We need the activity_get() methods of our views to return the
    object in question. So, if the view is based on a d-r-f class,
    we must wrap the result with this class.
    """

    def __init__(self, activity_value):
        super().__init__()

        self.activity_value = activity_value

    def __str__(self):
        return '<ActivityResponse, wrapping %s>' % (self.activity_value,)
