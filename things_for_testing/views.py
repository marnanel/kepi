from django.shortcuts import render
from django_kepi.views import *
from django_kepi.models import *
from things_for_testing.models import *

class ThingUserView(KepiView):
    def activity(self, *args, **kwargs):
        try:
            return ThingUser.objects.get(name=kwargs['name'])
        except ThingUser.DoesNotExist:
            return None

class ThingUserCollection(CollectionView):
    def get_collection_items(self, *args, **kwargs):
        return ThingUser.objects.all()

    def _stringify_object(self, obj):
        return obj.activity_form

class ThingUserFollowingView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Activity.objects.filter(
                f_type='Follow',
                f_actor=ThingUser(name=kwargs['name']).activity_id,
                accepted=True,
                )

    def _stringify_object(self, obj):
        return obj.f_object

class ThingUserFollowersView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Activity.objects.filter(
                f_type='Follow',
                f_object=ThingUser(name=kwargs['name']).activity_id,
                accepted=True,
                )

    def _stringify_object(self, obj):
        return obj.f_actor


