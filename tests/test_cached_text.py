from django.test import TestCase
from django_kepi.models import CachedText

class TestCachedText(TestCase):

    # Test cases?

    def test_create(self):

        TEST_URL = "https://shakespeare.example.com/sonnet"
        INCORRECT_URL = TEST_URL + "/not-this-one"
        TEST_CONTENTS = "Thou art more lovely and more temperate"
        
        c1 = CachedText(
                source = TEST_URL,
                contents = TEST_CONTENTS,
                )
        c1.save()

        c2 = CachedText.objects.get(
                source = TEST_URL,
                )

        self.assertEqual(c2.contents, TEST_CONTENTS)

        with self.assertRaises(CachedText.DoesNotExist):
            CachedText.objects.get(
                    source = INCORRECT_URL,
                    )


