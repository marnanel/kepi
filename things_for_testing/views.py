from django.shortcuts import render
from django_kepi.views import CollectionView
from things_for_testing.models import *

class ThingUserCollection(CollectionView):
    def get_collection_items(self, *args, **kwargs):
        return ThingUser.objects.all()

    def _stringify_object(self, obj):
        return obj.serialize()

