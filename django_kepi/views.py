from django_kepi import ATSIGN_CONTEXT
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django_kepi.models import Following
import urllib.parse
import json
import re

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

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

def _make_query_page(
        request,
        page_number,
        ):
    
    fields = dict(request.GET)

    if page_number is None:
        if PAGE_FIELD in fields:
            del fields[PAGE_FIELD]
    else:
        fields[PAGE_FIELD] = page_number

    encoded = urllib.parse.urlencode(fields)

    if encoded!='':
        encoded = '?'+encoded

    return '{}://{}{}{}'.format(
            request.scheme,
            request.get_host(),
            request.path,
            encoded,
            )

class CollectionView(django.views.View):

    class Meta:
        abstract = True

    def get(self, request, *args, **kwargs):

        items = self.get_collection_items(*args, **kwargs)
        # XXX assert that items.ordered

        our_url = request.build_absolute_uri()
        index_url = _make_query_page(request, None)
        
        if PAGE_FIELD in request.GET:

            page_number = int(request.GET[PAGE_FIELD])

            start = (page_number-1) * PAGE_LENGTH

            listed_items = items[start: start+PAGE_LENGTH]

            result = {
                    "@context": ATSIGN_CONTEXT,
                    "type" : "OrderedCollectionPage",
                    "id" : our_url,
                    "totalItems" : items.count(),
                    "orderedItems" : [str(x) for x in listed_items],
                    "partOf": index_url,
                    }

            if page_number > 1:
               result["prev"] = _make_query_page(request, page_number-1)

            if items.count() < (page_number*PAGE_LENGTH):
               result["next"] = _make_query_page(request, page_number+1)

        else:

            # Index page.

            result = {
                    "@context": ATSIGN_CONTEXT,
                    "type": "OrderedCollection",
                    "id": index_url,
                    "totalItems" : items.count(),
                    }

            if items.exists():
                    result["first"] = "{}?page=1".format(our_url,)

        return render(result)

    def get_collection_items(self, *args, **kwargs):
        return RuntimeError("not in the superclass")

class FollowersView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Following.objects.filter(following__name=kwargs['username'])

