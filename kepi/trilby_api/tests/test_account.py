from unittest import skip
from rest_framework.test import APIClient, force_authenticate
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from kepi.trilby_api.models import *
from django.conf import settings

# Tests for accounts. API docs are here:
# https://docs.joinmastodon.org/methods/accounts/

class TestAccountCredentials(TrilbyTestCase):

    # Getting the list of an account's statuses is handled in test_timeline.

    def test_verify_credentials_anonymous(self):
        result = self.get(
                '/api/v1/accounts/verify_credentials',
                expect_result = 401,
                )

    def test_get_user(self):
        alice = create_local_person(name='alice')

        content = self.get(
                '/api/v1/accounts/alice',
                as_user = alice,
                )

        self.assertIn('created_at', content)
        self.assertNotIn('email', content)

        for field, expected in ACCOUNT_EXPECTED.items():
            self.assertIn(field, content)
            self.assertEqual(content[field], expected,
                    msg="field '{}': got {}, expected {}".format(
                        field,
                        content[field],
                        expected,
                        ))

    @skip("I'll write this test later")
    def test_register(self):
        # FIXME not sure how to implement this test!
        pass
   
    def test_update_credentials(self):

        expected_fields = ACCOUNT_EXPECTED.copy()

        alice = create_local_person(name='alice')

        for delta in [

                {
                    'display_name': 'Thomas the Rhymer',
                },

                {
                    'display_name': 'Catherine of Aragon',
                },

                {},

                {
                    'note': 'I\'m a paragon of royalty',
                },

                {
                    'bot': True,
                },

                {
                    # try multiple fields
                    'note': 'So if you try to dump me...',
                    'bot': False,
                },

                {
                    'locked': True,
                    'bot': False, # so no change
                },

                {
                    'source[privacy]': 'public',
                },

                {
                    'source[privacy]': 'private',
                },

                {
                    'source[sensitive]': True,
                },

                {
                    'source[language]': 'cy',
                },

                ]:


            content = self.patch(
                    '/api/v1/accounts/update_credentials',
                    data = delta,
                    as_user = alice,
                    )

            for f,v in delta.items():
                expected_fields[f] = v

            for field, expected in expected_fields.items():

                if field.startswith('source['):
                    field = field[7:-1]
                    where = content['source']
                else:
                    where = content

                self.assertIn(field, where)
                self.assertEqual(where[field], expected,
                        msg="field '{}': got {}, expected {}".format(
                            field,
                            where[field],
                            expected,
                            ))

    @skip("Not yet implemented")
    def test_account_followers(self):
        pass

    @skip("Not yet implemented")
    def test_account_following(self):
        pass

    @skip("Not yet implemented")
    def test_account_in_lists(self):
        pass

    @skip("Not yet implemented")
    def test_account_relationships(self):
        pass

    @skip("Not yet implemented")
    def test_account_search(self):
        pass

class TestAccountActions(TrilbyTestCase):

    @skip("Not yet implemented")
    def test_follow(self):
        pass

    @skip("Not yet implemented")
    def test_unfollow(self):
        pass

    @skip("Not yet implemented")
    def test_block(self):
        pass

    @skip("Not yet implemented")
    def test_unblock(self):
        pass

    @skip("Not yet implemented")
    def test_mute(self):
        pass

    @skip("Not yet implemented")
    def test_unmute(self):
        pass

