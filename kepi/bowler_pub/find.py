# find.py
#
# Part of kepi, an ActivityPub daemon.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This module contains find(), which finds objects.
"""

from django.db import models
import requests
import logging
from django.conf import settings
import django.urls
from urllib.parse import urlparse
from django.http.request import HttpRequest
from kepi.bowler_pub.create import create
from django.utils import timezone
from kepi.bowler_pub.utils import is_short_id
import json
import mimeparse

logger = logging.getLogger(name='kepi')

class Fetch(models.Model):

    """
    A record of something having been fetched from a
    particular URL at a particular time. It doesn't
    contain the actual data; it just keeps the cache fresh.
    """

    url = models.URLField(
            primary_key = True,
            )

    date = models.DateTimeField(
            default = timezone.now,
            )

class ActivityRequest(HttpRequest):

    """
    These are fake HttpRequests which we send to the views
    as an ACTIVITY_GET or ACTIVITY_STORE method.

    For more information, see the docstring in views/.
    """

    def __init__(self, path, object_to_store):
        super().__init__()

        self.path = path

        if object_to_store is None:
            self.method = 'ACTIVITY_GET'
        else:
            self.method = 'ACTIVITY_STORE'
            self.activity = object_to_store

class TombstoneException(Exception):
    # XXX obsolete; remove
    def __init__(self, tombstone, *args, **kwargs):
        self.tombstone = tombstone
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.tombstone.__str__()

###################################

COLLECTION_TYPES = set([
    'OrderedCollection',
    'OrderedCollectionPage',
    ])

class Collection(dict):
    """
    The contents of a remote object of any type in COLLECTION_TYPES.
    """
    pass

###################################

def find_local(path,
        object_to_store=None):

    """
    Finds a local object and returns it.
    Optionally, passes it another object.

    path -- the path to the object. Note: not the URL.
        The URL is redundant because we know this object is local.
    object_to_store -- something to give the object when we find it.
        For example, if "path" refers to someone's inbox,
        "object_to_store" might be an activity to add to it.
    """

    from django.urls import resolve

    try:
        resolved = resolve(path)
    except django.urls.Resolver404:
        logger.debug('%s: -- not found', path)
        return None

    logger.debug('%s: handled by %s, %s, %s',
            path,
            str(resolved.func),
            str(resolved.args),
            str(resolved.kwargs),
            )

    request = ActivityRequest(
            path=path,
            object_to_store=object_to_store,
            )
    result = resolved.func(request,
            **resolved.kwargs)

    if result:
        logger.debug('%s: resulting in %s', path, str(result))

    return result

def find_remote(url,
        do_not_fetch=False,
        run_delivery=False):
    """
    Finds a remote object and returns it.
    We return None if the object couldn't be found, or was
    somehow invalid. Otherwise, we create a local copy of
    the object and return that. 

    As a special case, if the remote object is a collection type,
    we return a find.Collection (which is just a dict subclass)
    containing its fields.

    url -- the URL of the remote object.
    do_not_fetch -- True if we should give up and return None
        when the cache doesn't hold the remote object; False
        (the default) if we should go and get it via HTTP.
    run_delivery -- whether to deliver the found object to
        its stated audiences. This is usually not what you want.
    """

    from kepi.bowler_pub.models.acobject import AcObject 

    logger.debug('%s: find remote', url)

    try:
        fetch = Fetch.objects.get(
                url=url,
                )

        # TODO: cache timeouts.
        # FIXME: honour cache headers etc

        # We fetched it in the past.

        try:
            result = AcObject.objects.get(
                    id = url,
                    )
            logger.debug('%s: already fetched, and it\'s %s',
                    url, result)

            return result
        except AcObject.DoesNotExist:
            logger.debug('%s: we already know it wasn\'t there',
                    url)

            return None

    except Fetch.DoesNotExist:
        # We haven't fetched it before.
        # So we need to fetch it now.
        pass

    if do_not_fetch:
        logger.info('%s: do_not_fetch was set, so returning None',
                url)
        return None

    logger.info('%s: performing the GET', url)
    response = requests.get(url,
            headers={'Accept': 'application/activity+json'},
            )

    fetch_record = Fetch(url=url)
    fetch_record.save()

    if response.status_code!=200:
        logger.warn('%s: remote server responded %s %s' % (
            url,
            response.status_code, response.reason))
        return None

    mime_type = mimeparse.parse_mime_type(
            response.headers['Content-Type'])
    mime_type = '/'.join(mime_type[0:2])

    if mime_type not in [
        'application/activity+json',
        'application/json',
        'text/json',
        'text/plain',
        ]:
        logger.warn('%s: response had the wrong Content-Type, %s' % (
            url, response.headers['Content-Type'],
            ))
        return None

    logger.debug('%s: response was: %s' % (
        url, response.text,
        ))

    try:
        content = json.loads(response.text)
    except json.JSONDecodeError:
        logger.warn('%s: response was not JSON' % (
            url,
            ))
        return None

    if not isinstance(content, dict):
        logger.warn('%s: response was not a JSON dict' % (
            url,
            ))
        return None

    content_without_at = dict([
        (f, v)
        for f, v in content.items()
        if not f.startswith('@')
        ])

    if content['type'] in COLLECTION_TYPES:
        # It might be better if find() downloaded
        # an entire Collection if it finds the index.
        # At present we expect the caller to do it.
        result = Collection(content_without_at)
    else:
        result = create(
                is_local_user = False,
                value = content_without_at,
                id = url,
                run_delivery = run_delivery,
                )

    return result

def is_local(url):
    """
    True if "url" resides on the local server.

    False otherwise. Returns False even if
    the string argument is not in fact a URL.
    """
    if hasattr(url, 'url'):
        url = url.url

    if is_short_id(url):
        return True

    parsed_url = urlparse(url)
    return parsed_url.hostname in settings.ALLOWED_HOSTS

def _short_id_lookup(number):
    """
    Helper function to find an object when we actually have
    its short_id number.

    "number" is the number preceded by a slash
    (for example, "/2bad4dec"),
    or a name preceded by an atpersat
    (for example, "@alice").

    """

    from kepi.bowler_pub.models import AcObject

    try:
        result = AcObject.objects.get(
                id=number,
                )
        logger.debug('%s: found %s',
                number, result)

        return result

    except AcObject.DoesNotExist:
        logger.debug('%s: does not exist',
                number)

        return None

def find(url,
        local_only=False,
        do_not_fetch=False,
        object_to_store=None):
    """
    Finds an object.

    Keyword arguments:
    address -- the URL of the object. 
    local_only -- whether to restrict ourselves to local URLs.
    object_to_store -- if the address is a local collection,
        this is an object to add to that collection.

    If the address is local, we pass it to find_local(),
    which will look the object up using Django's usual dispatcher.
    If it isn't found, we return None.

    If the address is remote, we pass it to find_remote(),
    which will look for the object in the cache and return it.
    If it's not in the cache, and "do_not_fetch" is True,
    we return None. Otherwise, we fetch the object over HTTP.

    The reason for using "local_only" instead of just calling
    find_local() is that this function parses URLs for you.
    """

    if not url:
        return None

    if is_short_id(url):
        return _short_id_lookup(url)

    parsed_url = urlparse(url)
    is_local = parsed_url.hostname in settings.ALLOWED_HOSTS

    if is_local:
        return find_local(parsed_url.path,
                object_to_store=object_to_store)
    else:
        if local_only:
            logger.info('find: url==%s but is_local==False; ignoring',
                    url)
            return None

        return find_remote(
                url=url,
                do_not_fetch=do_not_fetch)
