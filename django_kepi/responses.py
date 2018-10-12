import django.http
import json
import django_kepi
import urllib

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class ActivityObjectResponse(django.http.HttpResponse):

    def __init__(self, item=None):

        super().__init__()

        self['Content-Type'] = 'application/activity+json'
        self._item = item

        if item is not None:
            try:
                result = item.activity_form

            except django_kepi.TombstoneException as tombstone:
                result = tombstone.activity_form
                self.status_code = 410 # Gone

            self._render(result)

    def _render(self, obj):
        json.dump(obj,
                fp=self,
                sort_keys=True,
                indent=2,
                )

class CollectionResponse(ActivityObjectResponse):

    def __init__(self,
            items,
            request):

        super().__init__()

        self.items = items

        our_url = request.build_absolute_uri()
        index_url = self._make_query_page(request, None)
        
        if PAGE_FIELD in request.GET:

            page_number = int(request.GET[PAGE_FIELD])

            start = (page_number-1) * PAGE_LENGTH

            listed_items = items[start: start+PAGE_LENGTH]

            result = {
                    "@context": django_kepi.ATSIGN_CONTEXT,
                    "type" : "OrderedCollectionPage",
                    "id" : our_url,
                    "totalItems" : items.count(),
                    "orderedItems" : [self.__transform_and_catch(x)
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
                    "@context": django_kepi.ATSIGN_CONTEXT,
                    "type": "OrderedCollection",
                    "id": index_url,
                    "totalItems" : items.count(),
                    }

            if items.exists():
                    result["first"] = "{}?page=1".format(our_url,)

        self._render(result)

    def get_collection_items(self, *args, **kwargs):
        # XXX use an actual abstract superclass
        return RuntimeError("not in the superclass")

    def __transform_and_catch(self, obj):
        try:
            return self._transform_object(obj)
        except django_kepi.TombstoneException as te:
            return te.activity_form

    def _transform_object(self, obj):
        return obj.activity_form

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

