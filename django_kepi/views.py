from django_kepi import ATSIGN_CONTEXT
from django_kepi.models import create
import django_kepi.validation
from django_kepi.find import find
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
from django_kepi.models import Thing, ThingField, Following, Actor
from collections.abc import Iterable
import logging
import urllib.parse
import json
import re
from collections import defaultdict

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

        if result is None:
            raise Http404()

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
                logger.warn("I don't know how to render objects like %s.", result)
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
            if 'id' in kwargs:
                logger.debug('Looking up Thing by id==%s',
                        kwargs['id'])
                activity_object = Thing.objects.get(
                        number=kwargs['id'],
                        )

            elif 'name' in kwargs:
                logger.debug('Looking up Thing by name==%s',
                        kwargs['name'])
                activity_object = Thing.objects.get(
                        f_name=kwargs['name'],
                        )
            else:
                raise ValueError("Need an id or a name")

        except Thing.DoesNotExist:
            logger.info('  -- unknown: %s', kwargs)
            return None
        except django.core.exceptions.ValidationError:
            logger.info('  -- invalid: %s', kwargs)
            return None

        result = activity_object
        logger.debug('  -- found object: %s', result)

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

class ActorView(ThingView):

    def activity(self, request, *args, **kwargs):
        thing = super().activity(request, *args, **kwargs)

        logger.debug('   -- found Thing %s; does it have an Actor?',
                thing)

        try:
            result = Actor.objects.get(
                    thing=thing,
                    )
            logger.debug('   -- yes, %s',
                    result)
            return result
        except Actor.DoesNotExist:
            logger.debug('   -- no')
            return None

class AllUsersView(KepiView):

    def activity(self, request, *args, **kwargs):

        logger.debug('Finding all users.')

        return Thing.objects.filter(f_type='Person')

    def _modify_list_item(self, obj):
        return obj.activity_form

########################################

class InboxView(django.views.View):

    def post(self, request, name=None, *args, **kwargs):

        # name is None for the shared inbox.

        if request.META['CONTENT_TYPE'] not in [
                'application/activity+json',
                'application/json',
                ]:
            return HttpResponse(
                    status = 415, # unsupported media type
                    )

        capture = django_kepi.validation.IncomingMessage(
                date = request.META['HTTP_DATE'],
                host = request.META['HOST'],
                path = request.path,
                signature = request.META['HTTP_SIGNATURE'],
                content_type = request.META['CONTENT_TYPE'],
                body = str(request.body, encoding='UTF-8'),
                )
        capture.save()
        logger.debug('%s: received %s with headers %s at %s -- now validating',
                capture,
                str(request.body, encoding='UTF-8'),
                dict(request.META.items()),
                request.path,
                )

        django_kepi.validation.validate(message_id=capture.id)
        logger.debug('%s: finished kicking off validation; returning to HTTP caller',
                capture,
                )

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )

    # We need to support GET (as a collection)
    # but we don't yet.

