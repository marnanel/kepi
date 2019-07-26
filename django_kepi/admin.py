from django.contrib import admin
from polymorphic.admin import *
from django_kepi.models import *

class ThingChildAdmin(PolymorphicChildModelAdmin):
    base_model = Thing

@admin.register(Actor)
class ActorChildAdmin(ThingChildAdmin):
        base_model = Actor

@admin.register(Item)
class ItemChildAdmin(ThingChildAdmin):
        base_model = Item

@admin.register(Activity)
class ActivityChildAdmin(ThingChildAdmin):
        base_model = Activity

@admin.register(Thing)
class ThingParentAdmin(PolymorphicParentModelAdmin):
    base_model = Thing
    child_models = (
            Actor,
            Item,
            Activity,
            )

class CollectionMemberInline(admin.TabularInline):
    model = CollectionMember

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    inlines = [
            CollectionMemberInline,
            ]
