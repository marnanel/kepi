from django_kepi import ATSIGN_CONTEXT, create as kepi_create
from django_kepi.validation import IncomingMessage
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
from django_kepi.models import Thing, ThingField, Following
from collections.abc import Iterable
import logging
import urllib.parse
import json
import re
from collections import defaultdict
from . import find

logger = logging.getLogger(name='django_kepi')

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class KepiView(django.views.View):

    def __init__(self):
        super().__init__()

        self.http_method_names.append('activity')

    def activity(self, request, *args, **kwargs):
        """
        Returns this view in a form suitable for ActivityPub.

        It may return:
         - a dict, suitable for turning into JSON
         - an iterable, such as a list or QuerySet;
              this will be turned into an OrderedCollection.
              Every member will be passed through
              _modify_list_item before rendering.
         - anything with a property called "activity_form";
           this value should be either an iterable or a dict,
           as above.

         This method is usually called by a KepiView's get() handler.
         By default, its args and kwargs will be passed in unchanged.

         It's also used to retrieve the ActivityPub form within
         the rest of the program, rather than as a response to
         a particular HTTP request. In that case, "request" will
         not be a real HttpRequest. (XXX so, what *will* it be?)

         Override this method in your subclass. In KepiView
         it's abstract.
        """
        raise NotImplementedError("implement activity() in a subclass: %s" % (
            self.__class__,
            ))

    def get(self, request, *args, **kwargs):
        """
        Returns a rendered HttpResult for a GET request.

        By default, KepiViews call self.activity() to get
        the data to render.
        """
        result = self.activity(request, *args, **kwargs)

        logger.debug('About to render object: %s',
                result)

        while True:
            if isinstance(result, dict):
                return self._render(result)

            if isinstance(result, Iterable):
                return self._collection_get(request, result)

            try:
                result = result.activity_form
                logger.debug(' -- it has an activity_form, %s; recurring',
                        result)
            except AttributeError:
                result.warn("I don't know how to render objects like %s.", result)
                raise ValueError("I don't know how to render objects like %s." % (result,))

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

    def _collection_get(self, request, items):

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
                    "orderedItems" : [self._modify_list_item(x)
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

    def _modify_list_item(self, obj):
        return str(obj)

class ThingView(KepiView):

    def activity(self, request, *args, **kwargs):

        try:
            activity_object = Thing.objects.get(
                    uuid=kwargs['id'],
                    )
        except Thing.DoesNotExist:
            logger.info('unknown: %s', kwargs['id'])
            return None
        except django.core.exceptions.ValidationError:
            logger.info('invalid: %s', kwargs['id'])
            return None

        result = activity_object.activity_form
        logger.debug('found object: %s', str(result))

        return result

class FollowingView(KepiView):

    def activity(self, request, *args, **kwargs):

        logger.debug('Finding following of %s:', kwargs['name'])

        person = Thing.objects.get(
                f_type='Person',
                f_name = kwargs['name'],
                )

        logging.debug('Finding followers of %s: %s',
                kwargs['name'], person)

        return Following.objects.filter(follower=person.url,
                pending=False)

    def _modify_list_item(self, obj):
        return obj.following

class FollowersView(KepiView):

    def activity(self, request, *args, **kwargs):

        logger.debug('Finding followers of %s:', kwargs['name'])

        person = Thing.objects.get(
                f_type='Person',
                f_name=kwargs['name'],
                )

        logging.debug('Finding followers of %s: %s',
                kwargs['name'], person)

        return Following.objects.filter(following=person.url,
                pending=False)

    def _modify_list_item(self, obj):
        return obj.follower

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

