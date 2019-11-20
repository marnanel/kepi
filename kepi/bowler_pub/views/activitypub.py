# views/activitypub.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
Various views. See views/README.md if you're wondering
about the ACTIVITY_* methods.

This module is too large and should be split up.
Everything ends up here if it doesn't have a particular
place to go.
"""

from kepi.bowler_pub import ATSIGN_CONTEXT
import kepi.bowler_pub.validation
from kepi.bowler_pub.find import find, is_local
from kepi.bowler_pub.utils import configured_url, short_id_to_url, uri_to_url
from django.shortcuts import render, get_object_or_404
import django.views
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.validation import validate
from collections.abc import Iterable
import logging
import urllib.parse
import json

logger = logging.getLogger(name='kepi')

PAGE_LENGTH = 50
PAGE_FIELD = 'page'

class KepiView(django.views.View):

    def __init__(self):
        super().__init__()

        self.http_method_names.extend([
                'activity_get',
                'activity_store',
                ])

    def activity_store(self, request, *args, **kwargs):
        """
        An internal request to store request.activity
        in whatever we happen to represent. No return
        value is expected: instead, throw an exception if
        there's a problem.
        """
        raise NotImplementedError(
            "I don't know how to store %s in %s." % (
                request.activity,
                request.path,
                ))

    def activity_get(self, request, *args, **kwargs):
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
        raise NotImplementedError("implement activity_get() in a subclass: %s" % (
            self.__class__,
            ))

    def post(self, request, *args, **kwargs):

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
                )

        return HttpResponse(
                status = 200,
                reason = 'Thank you',
                content = '',
                content_type = 'text/plain',
                )

    def get(self, request, *args, **kwargs):
        """
        Returns a rendered HttpResult for a GET request.

        By default, KepiViews call self.activity_get() to get
        the data to render.
        """
        result = self.activity_get(request, *args, **kwargs)

        if result is None:
            raise Http404()

        if isinstance(result, HttpResponse):
            logger.info('self.activity_get() returned HttpResponse %s',
                    result)
            return result

        return self._render_object(request, result)

    def _to_json(self, data):

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

    def _render_object(self, request, something):
        logger.debug('About to render object: %s of type %s',
                something, type(something))

        while True:
            try:
                something = something.activity_form
                logger.debug(' -- it has an activity_form, %s; iterating',
                        something)
                continue
            except AttributeError:
                break

        if isinstance(something, dict):
            logger.debug("  -- it's a dict; our work here is done") 
            return self._to_json(something)

        elif isinstance(something, Iterable):
            logger.debug("  -- it's an iterable; treating as a collection ") 
            return self._render_collection(request, something)

        logger.warn("I don't know how to render objects like %s.", something)
        raise ValueError("I don't know how to render objects like %s." % (something,))

    def _render_collection(self, request, items):

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

            count = items.count()

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

        return self._to_json(result)

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

    def _modify_list_item(self, obj):
        logger.debug('  -- default _modify_list_item for %s', obj)
        return self._render_object(obj)

class ThingView(KepiView):

    def activity_get(self, request, *args, **kwargs):

        try:
            logger.debug('Looking up Object by id==%s',
                    kwargs['id'])
            activity_object = AcObject.objects.get(
                    id='/'+kwargs['id'],
                    )

        except AcObject.DoesNotExist:
            logger.info('  -- unknown: %s', kwargs)
            return None
        except django.core.exceptions.ValidationError:
            logger.info('  -- invalid: %s', kwargs)
            return None

        result = activity_object
        logger.debug('  -- found object: %s', result)

        return result

class ActorView(ThingView):

    def activity_get(self, request, *args, **kwargs):

        self._username = kwargs['username']

        try:
            activity_object = AcActor.objects.get(
                    id='@'+kwargs['username'],
                    )

        except AcActor.DoesNotExist:
            logger.info('  -- unknown user: %s', kwargs)
            return None
        except django.core.exceptions.ValidationError:
            logger.info('  -- invalid: %s', kwargs)
            return None

        result = activity_object
        logger.debug('  -- found object: %s', result)

        return result

    def activity_store(self, request, *args, **kwargs):

        from kepi.bowler_pub.models.collection import Collection

        user = AcActor.objects.get(
                id='@'+kwargs['username'],
                )

        inbox = Collection.get(
                user = user,
                collection = 'inbox',
                create_if_missing = True,
                )

        logger.debug('%s: inbox: storing %s',
                user.id, request.activity)

        inbox.append(request.activity)

    def _to_json(self, data):
        """
        Adds the Link header to an Actor's record.

        The Link header is described in RFC 5988,
        and <https://www.w3.org/wiki/LinkHeader>.
        """

        result = super()._to_json(data)

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

class FollowingView(KepiView):

    def activity_get(self, request, *args, **kwargs):

        logger.debug('Finding following of %s:', kwargs['username'])

        user = configured_url('USER_LINK',
                username = kwargs['username'],
                )

        return Following.objects.filter(
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

        return Following.objects.filter(
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

class UserCollectionView(KepiView):

    _default_to_existing = False

    def activity_get(self, request,
            username,
            listname,
            *args, **kwargs):

        from kepi.bowler_pub.models.collection import Collection, CollectionMember

        logger.debug('Finding user %s\'s %s collection',
                username, listname)
        try:
            the_collection = Collection.objects.get(
                    owner__id = '@'+username,
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

    def activity_store(self, request,
            username,
            listname,
            *args, **kwargs):

        from kepi.bowler_pub.models.collection import Collection, CollectionMember

        logger.debug('Finding user %s\'s %s collection',
                username, listname)
        try:
            the_collection = Collection.objects.get(
                    owner__id = '@'+username,
                    name = listname)

            logger.debug('  -- found collection: %s. Appending %s.',
                the_collection, request.activity)

            the_collection.append(request.activity)

        except Collection.DoesNotExist:

            if self._default_to_existing:
                logger.debug('  -- does not exist; creating it')

                try:
                    owner = AcActor.objects.get(
                            id = '@'+username,
                    )
                except AcActor.DoesNotExist:
                    logger.debug('    -- but user %s doesn\'t exist; bailing',
                            username)
                    return

                the_collection = Collection(
                        owner = owner,
                        name = listname)

                the_collection.save()

                the_collection.append(request.activity)

                logger.debug('    -- done: collection is %s',
                        the_collection)

                return
            else:
                logger.debug('  -- does not exist; 404')
                raise Http404()

    def _modify_list_item(self, obj):
        return obj.member.activity_form

class InboxView(UserCollectionView):

    _default_to_existing = True

    # username can be None for the shared inbox.

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

    def activity_store(self, request,
            username=None, *args, **kwargs):

        from kepi.bowler_pub.delivery import deliver

        if username is None:
            logger.info('    -- storing into the shared inbox')

            # This is a bit of a hack, but I don't want people
            # submitting requests to the shared inbox which
            # ask to be submitted back to the shared inbox.
            if hasattr(request, 'no_multiplexing'):
                logger.info("        -- but we've been down this road before")
                return
            else:
                request.no_multiplexing = True

            recipients = sorted(set([url for urls in [
                urls for name,urls in request.activity.audiences.items()
                ] for url in urls]))

            for recipient in recipients:

                if not is_local(recipient):
                    logger.info('      -- recipient %s is remote; ignoring',
                            recipient)
                    continue

                logger.info('      -- recipient %s gets a copy',
                            recipient)

                deliver(
                        request.activity,
                        incoming = True,
                        )

            logger.info('    -- storing to shared inbox done')

        else:

            super().activity_store(
                    request,
                    username = username,
                    listname = 'inbox',
                    )

class OutboxView(UserCollectionView):

    _default_to_existing = True

    def activity_store(self, request,
            username, *args, **kwargs):
        super().activity_store(
                request,
                username = username,
                listname = 'outbox',
                )

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

        owner = configured_url('USER_LINK',
                username = kwargs['username'],
                )

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
