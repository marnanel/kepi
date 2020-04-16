from django.test import TestCase, Client
from rest_framework.test import force_authenticate, APIClient
from kepi.trilby_api.models import *
from django.conf import settings

class TrilbyTestCase(TestCase):

    def setUp(self):

        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

        super().setUp()

def create_local_person(name='jemima'):

    from kepi.trilby_api.models import TrilbyUser

    user = TrilbyUser(
            username = name,
            )
    user.save()

    result = Person(
            local_user = user,
            display_name = name,
            )
    result.save()

    return result

def create_local_status(content,
        posted_by,
        **kwargs,
        ):

    if isinstance(posted_by, TrilbyUser):
        posted_by = posted_by.person

    result = Status(
        remote_url = None,
        account = posted_by,
        content = content,
        **kwargs,
        )

    result.save()

    return result

def _client_request(
        url, data,
        as_user,
        is_post,
        ):

    c = APIClient()

    if as_user is not None:

        if isinstance(as_user, Person):
            as_user = as_user.local_user

        c.force_authenticate(as_user)

    if is_post:
        result = c.post(
                url,
                data,
                format = 'json',
                )
    else:
        result = c.get(
                url,
                format = 'json',
                )

    return result

def post(
        url,
        data,
        as_user = None):

    return _client_request(url, data, as_user,
            is_post = True)

def get(
        url,
        as_user = None):

    return _client_request(url, {}, as_user,
            is_post = False)

