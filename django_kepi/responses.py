import django.http
import json
import django_kepi

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class ActivityObjectResponse(django.http.HttpResponse):

    def __init__(self, item=None):

        super().__init__()

        self['Content-Type'] = 'application/activity+json'
        self._item = item

        if item is not None:
            try:
                result = item.activity

            except TombstoneException as tombstone:
                result = tombstone.activity
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

        super().__init__(self)

        self.items = items
        # assert that self.items is ordered

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
                    "orderedItems" : [self._transform_object(x)
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

    def _transform_object(self, obj):
        return str(obj)

