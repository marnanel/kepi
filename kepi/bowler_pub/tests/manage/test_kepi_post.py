from io import StringIO
from django.test import TestCase
from django.core.management import call_command
from kepi.bowler_pub.models import *
from .. import create_local_person

class KepiPostTest(TestCase):

    def test_list_simple(self):
        create_local_person('alice')

        out = StringIO()
        call_command(
                'kepi-post',
                '--actor', 'alice',
                'Turkey trots to water.',
                stdout=out)
        
        statuses = AcItem.objects.all()
        self.assertEqual(statuses.count(), 1)
        self.assertIn(
                'Turkey trots to water',
                statuses[0].text,
                )

        activities = AcActivity.objects.all()
        self.assertEqual(activities.count(), 1)
        self.assertEqual(
                activities[0]['object'],
                statuses[0].id,
                )

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

