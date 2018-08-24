from django_kepi import ATSIGN_CONTEXT
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
import urllib.parse
import json
import re

PAGE_LENGTH = 50

def render(data):
    # XXX merge in
    result = JsonResponse(
            data=data,
            json_dumps_params={
                'sort_keys': True,
                'indent': 2,
                }
            )

    result['Content-Type'] = 'application/activity+json'

    return result

class ActivityObjectView(django.views.View):

    def get(self, request, *args, **kwargs):

        #instance = ActivityObject.objects.get(pk=kwargs['id'])
        instance = None # XXX temp

        result = instance.serialize()

        return render(result)

########################

class CollectionView(django.views.View):

    class Meta:
        abstract = True

    def get(self, request, *args, **kwargs):

        items = self.get_collection_items(*args, **kwargs)

        our_url = request.build_absolute_url()
        our_url = urllib.parse.defrag(our_url)
        
        if PAGE_FIELD in request.GET:
            page_number = int(request.GET[PAGE_FIELD])

            start = (page_number-1) * PAGE_LENGTH

            listed_items = all_items[start: start+PAGE_LENGTH]

            result = {
                    "@context": ATSIGN_CONTEXT,
                    "type" : "OrderedCollectionPage",
                    "id" : our_url,
                    "totalItems" : items.count,
                    "orderedItems" : listed_items,
                    "partOf": our_url,
                    }

            if page_number > 1:
               result["prev"] = "{}?page={}".format(our_url, page_number-1)

            if items.count < (page_number*PAGE_LENGTH):
               result["next"] = "{}?page={}".format(our_url, page_number+1)

        else:
            result = {
                    "@context": ATSIGN_CONTEXT,
                    "type": "OrderedCollection",
                    "id": urldecode.defrag(our_url),
                    "totalItems" : items.count,
                    }

            if items.count!=0:
                    result["first"] = "{}?page=1".format(our_url,)

        return render(result)

    def get_collection_items(self, *args, **kwargs):
        return RuntimeError("not in the superclass")

class FollowersView(django.views.View):

    def get_collection_items(self, *args, **kwargs):
        return Following.objects.find(following=who)

