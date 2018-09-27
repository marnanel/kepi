from django.shortcuts import render
from django_kepi.views import *
from django_kepi.models import *
from things_for_testing.models import *

class ThingUserCollection(CollectionView):
    def get_collection_items(self, *args, **kwargs):
        return ThingUser.objects.all()

    def _stringify_object(self, obj):
        return obj.activity

class ThingUserFollowingView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Activity.objects.filter(
                f_type='Follow',
                f_actor=ThingUser(name=kwargs['name']).url,
                accepted=True,
                )

    def _stringify_object(self, obj):
        return ThingUser.objects.get(actor=obj.following).url

class ThingUserFollowersView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Activity.objects.filter(
                f_type='Follow',
                f_object=ThingUser(name=kwargs['name']).url,
                accepted=True,
                )

    def _stringify_object(self, obj):
        return ThingUser.objects.get(actor=obj.follower).url


