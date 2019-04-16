from django_kepi import ATSIGN_CONTEXT, create as kepi_create
from django_kepi.validation import IncomingMessage
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
import logging
import urllib.parse
import json
import re
from collections import defaultdict
from . import find

logger = logging.getLogger(name='django_kepi')

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class ActivityObjectView(django.views.View):

    def get(self, request, *args, **kwargs):

        url = 'https://' + \
                settings.KEPI['LOCAL_OBJECT_HOSTNAME'] + \
                request.path
        f_type = kwargs.get('f_type', None)

        activity_object = find(url, f_type)

        if activity_object is None:
            logger.info('%s(%s) is unknown', url, f_type)
            raise Http404('Unknown object')

        result = activity_object.activity_form(*args, **kwargs)

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

        headers = defaultdict(lambda: '',
                [(f[5:],v) for f,v in request.META.items() if f.startswith("HTTP_")])

        capture = IncomingMessage(
                date = headers['DATE'],
                host = headers[''],
                path = request.path,
                signature = headers['SIGNATURE'],
                body = str(request.body, encoding='UTF-8'),
                )
        capture.save()
        logger.debug('%s: received %s at %s',
                capture,
                str(request.body, encoding='UTF-8'),
                request.path,
                )

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )

    # We need to support GET (as a collection)
    # but we don't yet.

########################################

class AsyncResultView(django.views.View):

    def post(self, request, *args, **kwargs):

        uuid_passcode = request.GET['uuid']
        success = int(request.GET['success'])!=0

        if success:

            if not request.body:
                logger.warn('Batch notification had success==1 but no body')
                return django.http.HttpResponseBadRequest()

            body = str(request.body, encoding='UTF-8')

            # Why not use request.POST? Because the batch process might
            # reasonably use Content-Type: application/activity+json,
            # which Django wouldn't recognise as proper JSON, so
            # request.POST wouldn't get populated.

            # XXX we might want to check the Content-Type here

        else:

            if request.POST:
                logger.warn('Batch notification had success==0 but supplied a body')
                return django.http.HttpResponseBadRequest()

            body = None

        try:
            message_need = get_object_or_404(QuarantinedMessageNeeds, id=uuid_passcode)
        except ValidationError as e:
            logger.warn('Invalid UUID supplied: %s', uuid_passcode)
            raise e
        except QuarantinedMessageNeeds.NotFound as e:
            logger.warn('Batch notification for unknown UUID: %s',
                    uuid_passcode)
            raise e

        if success:
            logger.info('Batch processing has retrieved %s:',
                    message_need.needs_to_fetch)
            logger.debug(' -- its contents are %s', body)
        else:
            logger.info('Batch processing has failed to retrieve %s:',
                    message_need.needs_to_fetch)

        if success and body is not None:
            try:
                fields = json.loads(body)
                kepi_create(fields)
            except json.decoder.JSONDecodeError:
                fields = None
                success = False
                logger.warn('Body was not JSON. Treating as failure.')

        if success:
            logger.debug(' -- trying to deploy all matching messages again')
        else:
            logger.debug(' -- deleting all messages which relied on it')

        for need in list(QuarantinedMessageNeeds.objects.filter(
            needs_to_fetch = message_need.needs_to_fetch)):

            message = need.message
            need.delete()

            if success:
                logger.debug('    -- trying to deploy %s', str(need.message))
                message.deploy(retrying=True)
            else:
                logger.debug('    -- deleting %s', str(need.message))
                message.delete()

        logger.debug(' -- finished')

        return HttpResponse(
                status = 200,
                reason = 'All is well',
                content = '',
                content_type = 'text/plain',
                )

