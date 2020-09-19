from django.test import TestCase
from . import create_local_person, create_local_status

class TestReblog(TestCase):

    def test_reblogged(self):
        alice = create_local_person(
                name = "alice",
                )

        bob = create_local_person(
                name = "bob",
                )

        original = create_local_status(
                content = "Hello world",
                posted_by = alice,
                )

        self.assertFalse(
                original.reblogged,
                "Original status has initially not been reblogged",
                )

        reblog = create_local_status(
                content = original.content,
                posted_by = bob,
                reblog_of = original,
                )

        self.assertTrue(
                original.reblogged,
                "Original status has now been reblogged",
                )

    def test_original(self):
        alice = create_local_person(
                name = "alice",
                )

        bob = create_local_person(
                name = "bob",
                )

        original = create_local_status(
                content = "Hello world",
                posted_by = alice,
                )

        reblog = create_local_status(
                content = original.content,
                posted_by = bob,
                reblog_of = original,
                )

        self.assertEqual(
                original.original,
                original,
                "Original status is its own original",
                )

        self.assertEqual(
                reblog.original,
                original,
                "Original status is the original of the reblog",
                )

    def test_reblogs_count(self):
        alice = create_local_person(
                name = "alice",
                )

        bob = create_local_person(
                name = "bob",
                )

        original = create_local_status(
                content = "Hello world",
                posted_by = alice,
                )

        self.assertEqual(
                original.reblogs_count,
                0,
                "original starts with zero reblogs")

        for i in range(1, 20):

            reblog = create_local_status(
                    content = original.content,
                    posted_by = bob,
                    reblog_of = original,
                    )

            self.assertEqual(
                    original.reblogs_count,
                    i,
                    "Original reblogs increase",
                    )

            self.assertEqual(
                    reblog.reblogs_count,
                    0,
                    "Reblogs count of reblogs remains zero",
                    )
