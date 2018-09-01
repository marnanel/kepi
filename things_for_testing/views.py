from django.shortcuts import render
from django_kepi.views import CollectionView, FollowersView
from django_kepi.models import Following
from things_for_testing.models import *

class ThingUserCollection(CollectionView):
    def get_collection_items(self, *args, **kwargs):
        return ThingUser.objects.all()

    def _stringify_object(self, obj):
        return obj.serialize()

class ThingUserFollowersView(FollowersView):

    def get_collection_items(self, *args, **kwargs):
        kwargs['url'] = 'https://example.com/user/{}'.format(kwargs['name'])

        return super().get_collection_items(*args, **kwargs)

