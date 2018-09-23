from django_kepi import ATSIGN_CONTEXT, NeedToFetchException
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django_kepi.models import QuarantinedMessage
import urllib.parse
import json
import re

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class ActivityObjectView(django.views.View):

    def get(self, request, *args, **kwargs):

        result = self.objectDetails(*args, **kwargs)

        return self._render(result)

    def _make_query_page(
            self,
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

    def _render(self, data):
        result = JsonResponse(
                data=data,
                json_dumps_params={
                    'sort_keys': True,
                    'indent': 2,
                    }
                )

        result['Content-Type'] = 'application/activity+json'

        return result


class CollectionView(ActivityObjectView):

    def get(self, request, *args, **kwargs):

        items = self.get_collection_items(*args, **kwargs)
        # XXX assert that items.ordered

        our_url = request.build_absolute_uri()
        index_url = self._make_query_page(request, None)
        
        if PAGE_FIELD in request.GET:

            page_number = int(request.GET[PAGE_FIELD])

            start = (page_number-1) * PAGE_LENGTH

            listed_items = items[start: start+PAGE_LENGTH]

            result = {
                    "@context": ATSIGN_CONTEXT,
                    "type" : "OrderedCollectionPage",
                    "id" : our_url,
                    "totalItems" : items.count(),
                    "orderedItems" : [self._stringify_object(x)
                        for x in listed_items],
                    "partOf": index_url,
                    }

            if page_number > 1:
               result["prev"] = self._make_query_page(request, page_number-1)

            if start+PAGE_LENGTH < items.count():
               result["next"] = self._make_query_page(request, page_number+1)

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

        return self._render(result)

    def get_collection_items(self, *args, **kwargs):
        return kwargs['items']

    def _stringify_object(self, obj):
        return str(obj)

class FollowingView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Following.objects.filter(follower__url=kwargs['url'])

    def _stringify_object(self, obj):
        return obj.following.url

class FollowersView(CollectionView):

    def get_collection_items(self, *args, **kwargs):
        return Following.objects.filter(following__url=kwargs['url'])

    def _stringify_object(self, obj):
        return obj.follower.url

########################################

class InboxView(django.views.View):

    def post(self, request, name=None, *args, **kwargs):

        # username is None for the shared inbox.

        capture = QuarantinedMessage(
                username = name,
                body = str(request.body, encoding='UTF-8'),
                headers = '\n'.join(
                    ["%s: %s" for (f,v) in request.META.items() if f.startswith("HTTP_")],
                    ),
                )
        capture.save()

        try:
            capture.deploy()
        except NeedToFetchException:
            # we'll work it out later
            pass

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )

    # We need to support GET (as a collection)
    # but we don't yet.
