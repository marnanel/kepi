from django.contrib import admin
from polymorphic.admin import *
from django_kepi.models import *

class ObjectChildAdmin(PolymorphicChildModelAdmin):
    base_model = Object

@admin.register(Actor)
class ActorChildAdmin(ObjectChildAdmin):
        base_model = Actor

@admin.register(Item)
class ItemChildAdmin(ObjectChildAdmin):
        base_model = Item

@admin.register(Activity)
class ActivityChildAdmin(ObjectChildAdmin):
        base_model = Activity

@admin.register(Object)
class ObjectParentAdmin(PolymorphicParentModelAdmin):
    base_model = Object
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
