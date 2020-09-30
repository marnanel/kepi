# views/activitypub.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

from kepi.bowler_pub import ATSIGN_CONTEXT
import kepi.bowler_pub.validation
from kepi.bowler_pub.utils import *
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse, Http404
from kepi.bowler_pub.activityresponse import ActivityResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.validation import validate
import kepi.bowler_pub.serializers as bowler_serializers
import kepi.bowler_pub.renderers
import kepi.trilby_api.models as trilby_models
from collections.abc import Iterable
import logging
import urllib.parse
import json
from rest_framework import generics, response

logger = logging.getLogger(name='kepi')

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class KepiView(django.views.View):

    def __init__(self):
        super().__init__()

        self.http_method_names.extend([
                'activity_get',
                ])

    def activity_get(self, request, *args, **kwargs):
        """
        Returns this view in a form suitable for ActivityPub.

        It's used to retrieve the ActivityPub form within
        the rest of the program, rather than as a response to
        a particular HTTP request. In that case, "request" will
        not be a real HttpRequest from across the network;
        it'll be mocked up.

         Override this method in your subclass. In KepiView
         it's abstract.
        """
        raise NotImplementedError(
                "implement activity_get() in a subclass: %s" % (
            self.__class__,
            ))

    def get(self, request, *args, **kwargs):
        """
        Returns a rendered HttpResult for a GET request.

        By default, KepiViews call self.activity_get() to get
        the data to render.
        """
        result = self.activity_get(request, *args, **kwargs)

        if result is None:
            logger.debug('  -- activity_get returned None; 404')
            raise Http404()

        logger.debug('  -- activity_get returned %s (%s)',
                result, type(result))

        if isinstance(result, ActivityResponse):
            result = result.activity_value

        if isinstance(result, HttpResponse):
            logger.info('self.activity_get() returned HttpResponse %s',
                    result)
            return result

        data = self._render_object(result)

        log_one_message(
                direction=f"response to {request.path}",
                body=data,
                )

        httpresponse = self._to_httpresponse(data)
        return httpresponse

    def _to_httpresponse(self, data):

        if '@context' not in data:
            data['@context'] = ATSIGN_CONTEXT

        if 'former_type' in data:
            data['type'] = 'Tombstone'

        result = JsonResponse(
                data=data,
                json_dumps_params={
                    'sort_keys': True,
                    'indent': 2,
                    }
                )

        result['Content-Type'] = 'application/activity+json; charset=utf-8'

        if 'former_type' in data:
            result.reason = 'Entombed'
            result.status_code = 410

        return result

    def _render_object(self, something):
        return something

class PersonView(KepiView):

    def activity_get(self, request, *args, **kwargs):

        self._username = kwargs['username']

        try:
            person = trilby_models.LocalPerson.objects.get(
                    local_user__username = self._username,
                    )
            logger.debug('  -- found user: %s', person)
            return person

        except trilby_models.LocalPerson.DoesNotExist:
            logger.info('  -- unknown user: %s', kwargs)
            return None
        except django.core.exceptions.ValidationError:
            logger.info('  -- invalid: %s', kwargs)
            return None

    def _to_httpresponse(self, data):
        """
        Adds the Link header to an Actor's record.

        The Link header is described in RFC 5988,
        and <https://www.w3.org/wiki/LinkHeader>.
        """

        result = super()._to_httpresponse(data)

        user_url = configured_url('USER_LINK',
                username = self._username,
                )

        webfinger_url = uri_to_url(
            '/.well-known/webfinger?resource=%s' % (
                        urllib.parse.quote(
                            'acct:%(name)s@%(host)s' % {
                                'name': self._username,
                                'host': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                                })))

        atom_url = configured_url('USER_FEED_LINK',
                username = self._username,
                )

        links = [
                {
                    'url': webfinger_url,
                    'rel': 'lrdd',
                    'type': 'application/xrd+xml',
                    },

                {
                    'url': atom_url,
                    'rel': 'alternate',
                    'type': 'application/atom+xml',
                    },

                {
                    'url': user_url,
                    'rel': 'alternate',
                    'type': 'application/activity+json',
                    },
                ]

        link_value = ', '.join([
                    '<%(url)s>; rel="%(rel)s"; type="%(type)s"' % x
                    for x in links
                    ])

        logger.info('Setting Link header to: %s',
            link_value)

        result['Link'] = link_value

        return result

    def _render_object(self, something):
        serializer = bowler_serializers.PersonSerializer(
                something
                )
        return super()._render_object(serializer.data)

class FollowingView(KepiView):

    def activity_get(self, request, *args, **kwargs):

        logger.debug('Finding following of %s:', kwargs['username'])

        user = configured_url('USER_LINK',
                username = kwargs['username'],
                )

        return trilby_models.Follow.objects.filter(
                follower=user,
                pending=False)

    def _modify_list_item(self, obj):
        return obj.following

class FollowersView(KepiView):

    def activity_get(self, request, *args, **kwargs):

        logger.debug('Finding followers of %s:', kwargs['username'])

        user = configured_url('USER_LINK',
                username = kwargs['username'],
                )

        return trilby_models.Follow.objects.filter(
                following=user,
                pending=False)

    def _modify_list_item(self, obj):
        return obj.follower

class AllUsersView(KepiView):

    def activity_get(self, request, *args, **kwargs):

        logger.debug('Finding all users.')

        return AcActor.objects.all()

    def _modify_list_item(self, obj):
        return obj.activity_form

########################################

class CollectionView(generics.GenericAPIView):

    permission_classes = ()
    renderer_classes = [kepi.bowler_pub.renderers.ActivityRenderer]

    listname = None
    default_to_existing = True

    def _modify_list_item(self, obj):
        return obj

    def get(self, request,
            username,
            listname = None,
            *args, **kwargs):

        items = self.activity_get(request, username, listname,
                *args, **kwargs)

        if isinstance(items, ActivityResponse):
            items = items.activity_value

        # XXX assert that items.ordered

        our_url = request.build_absolute_uri()
        index_url = self._make_query_page_url(request, None)

        if PAGE_FIELD in request.GET:

            page_number = int(request.GET[PAGE_FIELD])
            logger.debug("    -- it's a request for page %d",
                    page_number)

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
               result["prev"] = self._make_query_page_url(request,
                       page_number-1)

            if start+PAGE_LENGTH < items.count():
               result["next"] = self._make_query_page_url(request,
                       page_number+1)

        else:

            # Index page.
            logger.debug("    -- it's a request for the index")

            count = len(items)

            result = {
                    "@context": ATSIGN_CONTEXT,
                    "type": "OrderedCollection",
                    "id": index_url,
                    "totalItems" : count,
                    }

            if count>0:
                    result["first"] = self._make_query_page_url(
                            request = request,
                            page_number = 1,
                            )

                    result["last"] = self._make_query_page_url(
                            request = request,
                            page_number = int(
                                1 + ((count+1)/PAGE_LENGTH),
                            ),
                            )

        return self._to_httpresponse(result)

    def activity_get(self, request,
            username,
            listname = None,
            *args, **kwargs):

        from kepi.trilby_api.models import LocalPerson, Status

        logger.debug('Finding user %s\'s %s collection',
                username, self.listname)

        result = None

        try:
            user = LocalPerson.objects.get(
                    local_user__username = username,
                    )
        except LocalPerson.DoesNotExist:
            logger.debug('  -- user does not exist')
            user = None

        if user is not None:
            method_name = f'get_{self.listname}_collection'

            if hasattr(user, method_name):
                method = getattr(user, method_name)
                result = method()
                logger.debug(
                        "  -- found %s(): %s",
                        method_name,
                        result,
                        )

            else:
                logger.warning(
                        "user does not have a %s method; this is weird",
                        method_name,
                        )

        if result is None:
            if self.default_to_existing:
                logger.debug('  -- collection does not exist')

                result = []
            else:
                logger.debug('  -- collection does not exist; 404')

                raise Http404()

        result = ActivityResponse(result)
        logger.debug('  -- result: %s', result)
        return result

    def _to_httpresponse(self, data):

        if '@context' not in data:
            data['@context'] = ATSIGN_CONTEXT

        if 'former_type' in data:
            data['type'] = 'Tombstone'

        result = JsonResponse(
                data=data,
                json_dumps_params={
                    'sort_keys': True,
                    'indent': 2,
                    }
                )

        result['Content-Type'] = 'application/activity+json; charset=utf-8'

        if 'former_type' in data:
            result.reason = 'Entombed'
            result.status_code = 410

        return result

    def _make_query_page_url(
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

    def _modify_list_item(self, item):
        serializer = bowler_serializers.CreateActivitySerializer(
                item,
                )
        return serializer.data

class OutboxView(CollectionView):

    listname = 'outbox'

class InboxView(CollectionView):

    listname = 'inbox'

    # FIXME: Only externally visible to the owner
    def activity_get(self, request, username=None, *args, **kwargs):

        if username is None:
            logger.info('Attempt to read from the shared inbox')
            return HttpResponse(
                    status = 403,
                    reason = 'The shared inbox is write-only',
                    )

        return super().activity_get(
                request,
                username = username,
                listname = 'inbox',
                )

    def post(self,
            request,
            username = None,
            *args, **kwargs):

        """
        Accept a message posted to one of our inboxes.

        All we do here is pass the message on to validate(),
        which will run asynchronously, and then thank the
        caller. There is no situation where the caller can
        get an error, because errors are being checked for
        behind the scenes by the validate() task.

        Params:
            request:  the HttpRequest
            username: the name of the owner of the inbox;
                      can be None for the shared inbox.
                      (We ignore this. There's nothing to
                      be gained by checking it.)
        """

        body = request.data

        log_one_message(
                direction = 'incoming',
                body = body,
        )

        try:
            validate(
                    path=request.path,
                    headers=request.headers,
                    body=body,
                    )
        except Exception as problem:
            import traceback

            log.warning("Processing this message caused an exception: %s %s",
                    problem,
                    ''.join(traceback.format_exception(
                        None, problem, problem.__traceback__)),
                    )

        # I think this should be 201 Created, but the spec
        # says 200, so 200 is what they get.
        return HttpResponse(
            status = 200,
            reason = "Thank you!",
            )
