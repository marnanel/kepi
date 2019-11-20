# admin.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These classes are used by the admin system to interact
with bowler_pub's models.
"""

from django.contrib import admin
from polymorphic.admin import *
from kepi.bowler_pub.models import *
from kepi.bowler_pub.validation import IncomingMessage
import kepi.bowler_pub.forms as bowler_pub_forms

###################################

@admin.register(AcActivity)
class ActivityAdmin(admin.ModelAdmin):
    child_models = (
        AcActivity, AcCreate, AcUpdate, AcDelete, AcFollow, AcAdd, AcRemove, \
                AcLike, AcUndo, AcAccept, AcReject, AcAnnounce,
                )

    base_model = AcActivity

@admin.register(AcNote)
class NoteAdmin(admin.ModelAdmin):
    form = bowler_pub_forms.NoteAdminForm
    base_model = AcNote

###################################

class CollectionMemberInline(admin.TabularInline):
    model = CollectionMember

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    inlines = [
            CollectionMemberInline,
            ]

@admin.register(IncomingMessage)
class IncomingMessageAdmin(admin.ModelAdmin):
    pass

@admin.register(Following)
class FollowingAdmin(admin.ModelAdmin):
    pass
