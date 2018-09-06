from django.shortcuts import render
from django_kepi.views import *
from django_kepi.models import Following
from things_for_testing.models import *

class ThingUserCollection(CollectionView):
    def get_collection_items(self, *args, **kwargs):
        return ThingUser.objects.all()

    def _stringify_object(self, obj):
        return obj.activity

class ThingUserFollowingView(FollowingView):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = 'https://example.com/user/{}'.format(kwargs['name'])

        return super().get_collection_items(*args, **kwargs)

    def _stringify_object(self, obj):
        return ThingUser.objects.get(actor=obj.following).name

class ThingUserFollowersView(FollowersView):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = 'https://example.com/user/{}'.format(kwargs['name'])

        return super().get_collection_items(*args, **kwargs)

    def _stringify_object(self, obj):
        return ThingUser.objects.get(actor=obj.follower).name


