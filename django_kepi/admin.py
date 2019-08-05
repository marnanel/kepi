from django.contrib import admin
from polymorphic.admin import *
from django_kepi.models import *
from django_kepi.validation import IncomingMessage
import django_kepi.forms as kepi_forms

###################################

class ObjectChildAdmin(PolymorphicChildModelAdmin):
    base_model = Object
    base_form = kepi_forms.ObjectAdminForm

###################################

# Why is this such an enormous faff?

@admin.register(Activity)
class ActivityChildAdmin(ObjectChildAdmin):
    child_models = (
        Activity, Create, Update, Delete, Follow, Add, Remove, \
                Like, Undo, Accept, Reject, Announce,
                )

    base_model = Activity

@admin.register(Create)
class CreateChildAdmin(ActivityChildAdmin):
    base_model = Create

@admin.register(Update)
class UpdateChildAdmin(ActivityChildAdmin):
    base_model = Update

@admin.register(Delete)
class DeleteChildAdmin(ActivityChildAdmin):
    base_model = Delete

@admin.register(Follow)
class FollowChildAdmin(ActivityChildAdmin):
    base_model = Follow

@admin.register(Add)
class AddChildAdmin(ActivityChildAdmin):
    base_model = Add

@admin.register(Remove)
class RemoveChildAdmin(ActivityChildAdmin):
    base_model = Remove

@admin.register(Like)
class LikeChildAdmin(ActivityChildAdmin):
    base_model = Like

@admin.register(Undo)
class UndoChildAdmin(ActivityChildAdmin):
    base_model = Undo

@admin.register(Accept)
class AcceptChildAdmin(ActivityChildAdmin):
    base_model = Accept

@admin.register(Reject)
class RejectChildAdmin(ActivityChildAdmin):
    base_model = Reject

@admin.register(Announce)
class AnnounceChildAdmin(ActivityChildAdmin):
    base_model = Announce

###################################

@admin.register(Actor)
class ActorChildAdmin(ObjectChildAdmin):

    child_models = (
        Application, Group, Organization, Person, Service,
        )
    base_model = Actor

@admin.register(Application)
class ApplicationChildAdmin(ActorChildAdmin):
    base_model = Application

@admin.register(Group)
class GroupChildAdmin(ActorChildAdmin):
    base_model = Group

@admin.register(Organization)
class OrganizationChildAdmin(ActorChildAdmin):
    base_model = Organization

@admin.register(Person)
class PersonChildAdmin(ActorChildAdmin):
    base_model = Person

@admin.register(Service)
class ServiceChildAdmin(ActorChildAdmin):
    base_model = Service

#####################################

@admin.register(Item)
class ItemChildAdmin(ObjectChildAdmin):
    base_model = Item

    child_models = (
            Article, Audio, Document, Event, Image, Note, \
            Page, Place, Profile, Relationship, Video,
        )

@admin.register(Article)
class ArticleChildAdmin(ItemChildAdmin):
    base_model = Article

@admin.register(Audio)
class AudioChildAdmin(ItemChildAdmin):
    base_model = Audio

@admin.register(Document)
class DocumentChildAdmin(ItemChildAdmin):
    base_model = Document

@admin.register(Event)
class EventChildAdmin(ItemChildAdmin):
    base_model = Event

@admin.register(Image)
class ImageChildAdmin(ItemChildAdmin):
    base_model = Image

@admin.register(Note)
class NoteChildAdmin(ItemChildAdmin):
    base_model = Note

@admin.register(Page)
class PageChildAdmin(ItemChildAdmin):
    base_model = Page

@admin.register(Place)
class PlaceChildAdmin(ItemChildAdmin):
    base_model = Place

@admin.register(Profile)
class ProfileChildAdmin(ItemChildAdmin):
    base_model = Profile

@admin.register(Relationship)
class RelationshipChildAdmin(ItemChildAdmin):
    base_model = Relationship

@admin.register(Video)
class VideoChildAdmin(ItemChildAdmin):
    base_model = Video

###################################

@admin.register(Object)
class ObjectParentAdmin(PolymorphicParentModelAdmin):
    base_model = Object
    child_models = (
            Create,
            Update,
            Delete,
            Follow,
            Add,
            Remove,
            Like,
            Undo,
            Accept,
            Reject,
            Announce,
            Application,
            Group,
            Organization,
            Person,
            Service,
            Article,
            Audio,
            Document,
            Event,
            Image,
            Note,
            Page,
            Place,
            Profile,
            Relationship,
            Video,
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
