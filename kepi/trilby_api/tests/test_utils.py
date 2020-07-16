from django.test import TestCase
from django.conf import settings
from kepi.trilby_api.utils import *

class TestUtils(TestCase):

    def setUp(self):
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def test_is_local_user_url(self):

        self.assertIsNone(
            find_local_view("https://testserver/i-like-wombats"),
            msg = "non-view gets None",
            )

        self.assertIsNone(
            find_local_view("https://silly.example.com/users/fred"),
            msg = "remote server gets None",
            )

        self.assertIsNone(
                find_local_view("My old man's a dustman"),
                msg = "invalid URL gets None",
                )

        view = find_local_view("https://testserver/users/fred")

        self.assertIsNotNone(
                view,
                msg = "URL for local user view is found",
                )

        self.assertEqual(
                view.func.__name__,
                "PersonView",
                msg = "URL for local user view gets the correct view",
                )

        self.assertEqual(
                view.kwargs['username'],
                "fred",
                msg = "URL for local user view gets the correct username",
                )

        view = find_local_view("https://testserver/users/fred/followers")

        self.assertIsNotNone(
                view,
                msg = "URL for local followers view is found",
                )

        self.assertEqual(
                view.func.__name__,
                "FollowersView",
                msg = "URL for local followers view gets the correct view",
                )

        self.assertEqual(
                view.kwargs['username'],
                "fred",
                msg = "URL for local followers view gets the correct username",
                )

        self.assertIsNotNone(
                find_local_view("https://testserver/users/fred",
                    which_views = ['PersonView'],
                    ),
                msg = "user view is found when which_views contains PersonView",
                )

        self.assertIsNotNone(
                find_local_view("https://testserver/users/fred",
                    which_views = ['PersonView', 'BlueMeanies'],
                    ),
                msg = "user view is found when which_views contains "+\
                        "PersonView and other things",
                )

        self.assertIsNone(
                find_local_view("https://testserver/users/fred",
                    which_views = [],
                    ),
                msg = "user view is found when which_views is the empty list",
                )
