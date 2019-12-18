from django.test import TestCase
from rest_framework.test import force_authenticate, APIClient, APIRequestFactory
from kepi.trilby_api.views import *
from kepi.trilby_api.tests import *
from django.conf import settings

class TestNotifications(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()
        settings.KEPI['LOCAL_OBJECT_HOSTNAME'] = 'testserver'

    def test_follow(self):
        alice = create_local_trilbyuser(name='alice')
        request = self.factory.get(
                '/api/v1/notifications/',
                )
        force_authenticate(request, user=alice)

        view = Notifications.as_view()
        result = view(request)
        result.render()

        self.assertEqual(
                result.status_code,
                200,
                msg = result.content,
                )

        content = json.loads(result.content.decode())


