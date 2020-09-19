from django.test import TestCase, Client
from rest_framework.test import force_authenticate, APIClient
from kepi.trilby_api.models import *
from django.conf import settings
import json

ACCOUNT_EXPECTED = {
        'username': 'alice',
        'acct': 'alice',
        'display_name': 'alice',
        'locked': False,

        'followers_count': 0,
        'following_count': 0,
        'statuses_count': 0,
        'note': '',
        'url': 'https://testserver/users/alice',
        'uri': 'https://testserver/users/alice',
        'fields': [],
        'emojis': [],

        'avatar': 'https://testserver/static/defaults/avatar_1.jpg',
        'header': 'https://testserver/static/defaults/header.jpg',
        'avatar_static': 'https://testserver/static/defaults/avatar_1.jpg',
        'header_static': 'https://testserver/static/defaults/header.jpg',

        'bot': False,
        }

ACCOUNT_SOURCE_EXPECTED = {
        'privacy': 'A',
        'sensitive': False,
        'language': settings.KEPI['LANGUAGES'][0], # FIXME
        }

STATUS_EXPECTED = {
        'in_reply_to_account_id': None,
        'content': '<p>Hello world.</p>',
        'emojis': [],
        'reblogs_count': 0,
        'favourites_count': 0,
        'reblogged': False,
        'favourited': False,
        'muted': False,
        'sensitive': False,
        'spoiler_text': '',
        'visibility': 'A',
        'media_attachments': [],
        'mentions': [],
        'tags': [],
        'card': None,
        'poll': None,
        # FIXME: See the note about "application" in
        # trilby_api/serializers.py.
        # 'application': None,
        'language': 'en',
        'pinned': False,
        }

class TrilbyTestCase(TestCase):

    def setUp(self):

        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

        super().setUp()

    def _create_alice(self):

        # TODO: this should be replaced with a general-case "_create_user()"
        # that then gets used everywhere

        result = create_local_person('alice')
        self._alice = result
        return result

    def request(self, verb, path,
            data={},
            as_user=None,
            expect_result=200,
            parse_result=True,
            *args, **kwargs,
            ):

        c = APIClient()

        if as_user:
            c.force_authenticate(as_user.local_user)

        command = getattr(c, verb)

        result = command(
                path=path,
                data=data,
                format='json',
                *args,
                **kwargs,
                )

        if expect_result is not None:
            self.assertEqual(
                    result.status_code,
                    expect_result,
                    msg = f"Got {result.status_code} from "+\
                            f"{path}; expected {expect_result}.",
                    )

        if parse_result:
            result = json.loads(result.content)

        return result

    def get(self, *args, **kwargs):
        return self.request('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request('post', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request('patch', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request('delete', *args, **kwargs)

def create_local_person(name='jemima',
        load_default_keys_from='kepi/bowler_pub/tests/keys/keys-0003.json',
        **kwargs):

    if 'publicKey' or 'privateKey' not in kwargs:
        keys = json.load(open(load_default_keys_from, 'r'))

        if 'publicKey' not in kwargs:
            kwargs['publicKey'] = keys['public']

        if 'privateKey' not in kwargs:
            kwargs['privateKey'] = keys['private']

    result = LocalPerson(
            username = name,
            **kwargs,
            )
    result.save()

    return result

def create_local_status(
        content = 'This is just a test',
        posted_by = None,
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

def create_local_like(
        liked_by,
        **kwargs):

    note = create_local_status()

    result = Like(
            liker = note,
            liked = liked_by,
            )

    return result
