from django_kepi import ATSIGN_CONTEXT
import django_kepi.validation
from django_kepi.find import find
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
from django_kepi.models import *
from django_kepi.validation import validate
from collections.abc import Iterable
import logging
import urllib.parse
import json

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

        if data['type']=='Tombstone':
            result.reason = 'Entombed'
            result.status_code = 410

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
                logger.debug('Looking up Actor by name==%s',
                        kwargs['name'])
                activity_object = Actor.objects.get(
                        f_preferredUsername=json.dumps(kwargs['name']),
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

        person = Actor.objects.get(
                f_preferredUsername=kwargs['name'],
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

        person = Actor.objects.get(
                f_preferredUsername=kwargs['name'],
                )

        logging.debug('Finding followers of %s: %s',
                kwargs['name'], person)

        return Following.objects.filter(following=person.url,
                pending=False)

    def _modify_list_item(self, obj):
        return obj.follower

class AllUsersView(KepiView):

    def activity(self, request, *args, **kwargs):

        logger.debug('Finding all users.')

        return Thing.objects.filter(f_type='Person')

    def _modify_list_item(self, obj):
        return obj.activity_form

########################################

class UserCollectionView(KepiView):

    _default_to_existing = False

    def activity(self, request,
            username,
            listname,
            *args, **kwargs):

        from django_kepi.models.collection import Collection, CollectionMember

        logger.debug('Finding user %s\'s %s collection',
                username, listname)
        try:
            the_collection = Collection.objects.get(
                    owner__f_preferredUsername = json.dumps(username),
                    name = listname)

            logger.debug('  -- found collection: %s',
                the_collection)

            return CollectionMember.objects.filter(
                    parent = the_collection,
                    )

        except Collection.DoesNotExist:

            if self._default_to_existing:
                logger.debug('  -- does not exist; returning empty')

                return CollectionMember.objects.none()
            else:
                logger.debug('  -- does not exist; 404')

                raise Http404()

    def _modify_list_item(self, obj):
        return obj.member.activity_form

class InboxView(UserCollectionView):

    _default_to_existing = True

    # FIXME: Only externally visible to the owner
    def activity(self, request, name=None, *args, **kwargs):

        if name is None:
            logger.info('Attempt to write to the shared inbox')
            return HttpResponse(
                    status = 403,
                    reason = 'The shared inbox is write-only',
                    )

        return super().activity(
                request,
                username = name,
                listname = 'inbox',
                )

    def post(self, request, name=None, *args, **kwargs):

        # name is None for the shared inbox.

        if request.headers['Content-Type'] not in [
                'application/activity+json',
                'application/json',
                ]:
            return HttpResponse(
                    status = 415, # unsupported media type
                    reason = 'Try application/activity+json',
                    )

        try:
            fields = json.loads(
                    str(request.body, encoding='UTF-8'))
        except json.decoder.JSONDecodeError:
            return HttpResponse(
                    status = 415, # unsupported media type
                    reason = 'Invalid JSON',
                    )
        except UnicodeDecodeError:
            return HttpResponse(
                    status = 400, # bad request
                    reason = 'Invalid UTF-8',
                    )

        validate(
                path = request.path,
                headers = request.headers,
                body = request.body,
                # is_local_user is used by create() to
                # determine whether to strip or require the
                # "id" field.
                # FIXME it probably shouldn't always be False here.
                is_local_user = False,
                target_collection = Collection.build_name(
                    username=name,
                    collectionname='inbox',
                    ),
                )

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )

class OutboxView(UserCollectionView):

    _default_to_existing = True

    def post(self, request, *args, **kwargs):
        logger.debug('Outbox: received %s',
                str(request.body, 'UTF-8'))
        logger.debug('Outbox: with headers %s',
                request.headers)

        try:
            fields = json.loads(request.body)
        except json.JSONDecoderError:
            logger.info('Outbox: invalid JSON; dropping')
            return HttpResponse(
                    status = 400,
                    reason = 'Invalid JSON',
                    content = 'Invalid JSON',
                    content_type = 'text/plain',
                    )

        actor = fields.get('actor', None)
        if actor is None:
            actor = fields.get('attributedTo', None)

        owner = settings.KEPI['USER_URL_FORMAT'] % (kwargs['username'],)

        if actor != owner:
            logger.info('Outbox: actor was %s but we needed %s',
                    actor, owner)

            return HttpResponse(
                    status = 410,
                    reason = 'Not yours',
                    content = 'Sir, you are an interloper!',
                    content_type = 'text/plain',
                    )

        validate(
                path = request.path,
                headers = request.headers,
                body = request.body,
                is_local_user = True,
                )

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )
