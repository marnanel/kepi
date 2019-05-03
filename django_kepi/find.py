from django.db import models
import requests
import logging
from django.conf import settings
import django.urls
from urllib.parse import urlparse
from django.http.request import HttpRequest

logger = logging.getLogger(name='django_kepi')

class CachedRemoteText(models.Model):

    address = models.URLField(
            primary_key = True,
            )

    content = models.TextField(
            default = None,
            null = True,
            )
    # XXX We should probably also have a cache timeout

    def is_gone(self):
        return self.content is None

    def __str__(self):
        if self.key is None:
            return '(%s: "%s")' % (self.owner, self.content[:20])
        else:
            return '(%s is GONE)' % (self.owner)

    @classmethod
    def fetch(cls,
            fetch_url,
            post_data):
        """
        Fetch a file over HTTPS (and other protocols).
        This function blocks; don't call it while
        serving a request.

        fetch_url: the URL of the file you want.
            FIXME: What happens if fetch_url is local?

        post_data: If this is a dict, then the request
            will be a POST, with the contents of
            that dict as parameters to the remote server.
            If this is None, then the request will
            be a GET.

        Returns: None, if post_data was a dict.
            If post_data was None, returns a CachedRemoteText.
            If fetch_url existed in the cache, this will be the cached 
            record; otherwise it will be a new record, which
            has already been saved.

            If the request was not successful, the is_gone()
            method of the returned CachedRemoteText will return True.
            All error codes, including notably 404, 410, and 500,
            are handled alike. (Is there any reason not to do this?)

            FIXME: What does it do if the request returned a redirect?

        """

        if post_data is None:

            # This is a GET, so the answer might be cached.
            # (FIXME: honour HTTP caching headers etc)
            existing = cls.objects.find(address==fetch_url)
            if existing is not None:
                logger.info('fetch %s: in cache', fetch_url)
                return existing

            logger.info('fetch %s: GET', fetch_url)

            fetch = requests.get(fetch_url)
        else:
            logger.info('fetch %s: POST', fetch_url)
            logger.debug('fetch %s: with data: %s',
                    fetch_url, post_data)

            fetch = requests.post(fetch_url,
                    data=post_data)

        logger.info('fetch %s: response code was %d',
                fetch_url, fetch.status_code, fetch.text)
        logger.debug('fetch %s: body was %d',
                fetch_url, fetch.text)

        result = None

        if post_data is None:
            # This was a GET, so cache it
            # (FIXME: honour HTTP caching headers etc)
            # XXX: race condition: catch duplicate entry exception and ignore

            if fetch.status_code==200:
                content = fetch.text
            else:
                content = None

            result = cls(
                    address = fetch_url,
                    content = content,
                    )
            result.save()

        return result

    def _obviously_belongs_to(self, actor):
        return self.address.startswith(actor+'#')

class ActivityRequest(HttpRequest):

    def __init__(self):
        super().__init__()

        self.method = 'ACTIVITY'

def find_local(path):
    logger.debug('%s: find local', path)

    try:
        resolved = django.urls.resolve(path)
    except django.urls.Resolver404:
        logger.debug('%s: -- not found', path)
        return None

    logger.debug('%s: handled by %s', path, str(resolved.func))
    logger.debug('%s: %s', path, str(resolved.args))
    logger.debug('%s: %s', path, str(resolved.kwargs))

    request = ActivityRequest()
    result = resolved.func(request,
            **resolved.kwargs)
    logger.debug('%s: resulting in %s', path, str(result))

    return result

def find_remote(url):
    logger.debug('%s: find remote', url)
    return None # XXX

def find(url):
    """
    Finds an object.

    address: the URL of the object. 

    If the address is local, we look the object up using
    Django's usual dispatcher.

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
        return find_remote(url)
