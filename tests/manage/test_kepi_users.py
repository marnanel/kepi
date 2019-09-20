from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from .. import create_local_person

class KepiUsersTest(TestCase):

    def test_list_no_users(self):
        out = StringIO()
        call_command(
                'kepi-users',
                stdout=out)
        self.assertIn(
                'No users found',
                out.getvalue())
        self.assertNotIn(
                'Which user are you?',
                out.getvalue())

    def test_list_users(self):

        create_local_person('alice')
        create_local_person('bob')

        out = StringIO()
        call_command(
                'kepi-users',
                stdout=out)
        self.assertIn(
                '@alice',
                out.getvalue())
        self.assertIn(
                '@bob',
                out.getvalue())
        self.assertNotIn(
                'No users found',
                out.getvalue())

    def test_create_user(self):

        out = StringIO()
        call_command(
                'kepi-users',
                stdout=out)
        self.assertIn(
                'No users found',
                out.getvalue())

        out = StringIO()
        call_command(
                'kepi-users',
                '--create',
                'hildegard',
                stdout=out)

        out = StringIO()
        call_command(
                'kepi-users',
                stdout=out)
        self.assertIn(
                '@hildegard',
                out.getvalue())
        self.assertNotIn(
                'No users found',
                out.getvalue())

