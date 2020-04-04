# admin.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These classes are used by the admin system to interact
with bowler_pub's models.
"""

from django.contrib import admin
from kepi.bowler_pub.models import *

@admin.register(Incoming)
class IncomingAdmin(admin.ModelAdmin):
    pass
