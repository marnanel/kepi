# admin.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
These classes are used by the admin system to interact
with kepi's models.
"""

from django.contrib import admin
from polymorphic.admin import *
from django_kepi.models import *
from django_kepi.validation import IncomingMessage
import django_kepi.forms as kepi_forms

###################################

class ObjectChildAdmin(PolymorphicChildModelAdmin):
    base_model = AcObject
    base_form = kepi_forms.ObjectAdminForm

###################################

# Why is this such an enormous faff?

@admin.register(AcActivity)
class ActivityChildAdmin(ObjectChildAdmin):
    child_models = (
        AcActivity, AcCreate, AcUpdate, AcDelete, AcFollow, AcAdd, AcRemove, \
                AcLike, AcUndo, AcAccept, AcReject, AcAnnounce,
                )

    base_model = AcActivity

@admin.register(AcCreate)
class CreateChildAdmin(ActivityChildAdmin):
    base_model = AcCreate

@admin.register(AcUpdate)
class UpdateChildAdmin(ActivityChildAdmin):
    base_model = AcUpdate

@admin.register(AcDelete)
class DeleteChildAdmin(ActivityChildAdmin):
    base_model = AcDelete

@admin.register(AcFollow)
class FollowChildAdmin(ActivityChildAdmin):
    base_model = AcFollow

@admin.register(AcAdd)
class AddChildAdmin(ActivityChildAdmin):
    base_model = AcAdd

@admin.register(AcRemove)
class RemoveChildAdmin(ActivityChildAdmin):
    base_model = AcRemove

@admin.register(AcLike)
class LikeChildAdmin(ActivityChildAdmin):
    base_model = AcLike

@admin.register(AcUndo)
class UndoChildAdmin(ActivityChildAdmin):
    base_model = AcUndo

@admin.register(AcAccept)
class AcceptChildAdmin(ActivityChildAdmin):
    base_model = AcAccept

@admin.register(AcReject)
class RejectChildAdmin(ActivityChildAdmin):
    base_model = AcReject

@admin.register(AcAnnounce)
class AnnounceChildAdmin(ActivityChildAdmin):
    base_model = AcAnnounce

###################################

@admin.register(AcActor)
class ActorChildAdmin(ObjectChildAdmin):

    child_models = (
        AcApplication, AcGroup, AcOrganization, AcPerson, AcService,
        )
    base_model = AcActor

@admin.register(AcApplication)
class ApplicationChildAdmin(ActorChildAdmin):
    base_model = AcApplication

@admin.register(AcGroup)
class GroupChildAdmin(ActorChildAdmin):
    base_model = AcGroup

@admin.register(AcOrganization)
class OrganizationChildAdmin(ActorChildAdmin):
    base_model = AcOrganization

@admin.register(AcPerson)
class PersonChildAdmin(ActorChildAdmin):
    base_model = AcPerson

@admin.register(AcService)
class ServiceChildAdmin(ActorChildAdmin):
    base_model = AcService

#####################################

@admin.register(AcItem)
class ItemChildAdmin(ObjectChildAdmin):
    base_model = AcItem

    child_models = (
            AcArticle, AcAudio, AcDocument, AcEvent, AcImage, AcNote,\
            AcPage, AcPlace, AcProfile, AcRelationship, AcVideo,
        )

@admin.register(AcArticle)
class ArticleChildAdmin(ItemChildAdmin):
    base_model = AcArticle

@admin.register(AcAudio)
class AudioChildAdmin(ItemChildAdmin):
    base_model = AcAudio

@admin.register(AcDocument)
class DocumentChildAdmin(ItemChildAdmin):
    base_model = AcDocument

@admin.register(AcEvent)
class EventChildAdmin(ItemChildAdmin):
    base_model = AcEvent

@admin.register(AcImage)
class ImageChildAdmin(ItemChildAdmin):
    base_model = AcImage

@admin.register(AcNote)
class NoteChildAdmin(ItemChildAdmin):
    base_model = AcNote

@admin.register(AcPage)
class PageChildAdmin(ItemChildAdmin):
    base_model = AcPage

@admin.register(AcPlace)
class PlaceChildAdmin(ItemChildAdmin):
    base_model = AcPlace

@admin.register(AcProfile)
class ProfileChildAdmin(ItemChildAdmin):
    base_model = AcProfile

@admin.register(AcRelationship)
class RelationshipChildAdmin(ItemChildAdmin):
    base_model = AcRelationship

@admin.register(AcVideo)
class VideoChildAdmin(ItemChildAdmin):
    base_model = AcVideo

###################################

@admin.register(AcObject)
class ObjectParentAdmin(PolymorphicParentModelAdmin):
    base_model = AcObject
    child_models = (
            AcCreate,
            AcUpdate,
            AcDelete,
            AcFollow,
            AcAdd,
            AcRemove,
            AcLike,
            AcUndo,
            AcAccept,
            AcReject,
            AcAnnounce,
            AcApplication,
            AcGroup,
            AcOrganization,
            AcPerson,
            AcService,
            AcArticle,
            AcAudio,
            AcDocument,
            AcEvent,
            AcImage,
            AcNote,
            AcPage,
            AcPlace,
            AcProfile,
            AcRelationship,
            AcVideo,
            )
    list_filter = (PolymorphicChildModelFilter, )

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
