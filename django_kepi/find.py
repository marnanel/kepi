from django.db import models
import requests
import logging
from django.conf import settings
import django.urls
from urllib.parse import urlparse
from django.http.request import HttpRequest
from django_kepi.create import create
import datetime
import json
import mimeparse

logger = logging.getLogger(name='django_kepi')

class Fetch(models.Model):

    url = models.URLField(
            primary_key = True,
            )

    date = models.DateTimeField(
            default = datetime.datetime.now,
            )

class ThingRequest(HttpRequest):

    def __init__(self, path, object_to_store):
        super().__init__()

        self.path = path

        if object_to_store is None:
            self.method = 'ACTIVITY_GET'
        else:
            self.method = 'ACTIVITY_STORE'
            self.activity = object_to_store

class TombstoneException(Exception):
    def __init__(self, tombstone, *args, **kwargs):
        self.tombstone = tombstone
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.tombstone.__str__()

def find_local(path,
        object_to_store=None):

    try:
        resolved = django.urls.resolve(path)
    except django.urls.Resolver404:
        logger.debug('%s: -- not found', path)
        return None

    logger.debug('%s: handled by %s, %s, %s',
            path,
            str(resolved.func),
            str(resolved.args),
            str(resolved.kwargs),
            )

    request = ThingRequest(
            path=path,
            object_to_store=object_to_store,
            )
    result = resolved.func(request,
            **resolved.kwargs)

    if result:
        logger.debug('%s: resulting in %s', path, str(result))

    return result

def find_remote(url,
        do_not_fetch=False):

    from django_kepi.models.thing import Object 

    logger.debug('%s: find remote', url)

    try:
        fetch = Fetch.objects.get(
                url=url,
                )

        # TODO: cache timeouts.
        # FIXME: honour cache headers etc

        # We fetched it in the past.

        try:
            result = Object.objects.get(
                    remote_url = url,
                    )
            logger.debug('%s: already fetched, and it\'s %s',
                    url, result)

            return result
        except Object.DoesNotExist:
            logger.debug('%s: we already know it wasn\'t there',
                    url)

            return None

    except Fetch.DoesNotExist:
        # We haven't fetched it before.
        # So we need to fetch it now.
        pass

    if do_not_fetch:
        logger.info('%s: do_not_fetch was set, so returning None')
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

    content_with_f = dict([
        ('f_'+f, v)
        for f, v in content.items()
        if not f.startswith('@')
        ])

    result = create(
            is_local_user = False,
            **content_with_f,
            remote_url = url,
            )

    return result

def is_local(url):
    parsed_url = urlparse(url)
    return parsed_url.hostname in settings.ALLOWED_HOSTS

def find(url,
        local_only=False,
        do_not_fetch=False):
    """
    Finds an object.

    address: the URL of the object. 
    local_only: whether to restrict ourselves to local URLs.

    If the address is local, we look the object up using
    Django's usual dispatcher.

    If it isn't found, and local_only is set, we return None.

    Otherwise, we check the cache. If the JSON source of the
    object is in the cache, we parse it and return it.

    Otherwise, we dereference the URL.

    The result can be None, if the object doesn't exist locally
    or isn't found remotely, and for remote objects this fact
    may be cached.

    Results other than None are guaranteed to be subscriptable.
    """

    parsed_url = urlparse(url)
    is_local = parsed_url.hostname in settings.ALLOWED_HOSTS

    if is_local:
        return find_local(parsed_url.path)
    else:
        if local_only:
            logger.info('find: url==%s but is_local==False; ignoring',
                    url)
            return None

        return find_remote(
                url=url)
