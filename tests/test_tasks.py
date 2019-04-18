from django.test import TestCase, Client
from django_kepi.validation import CachedRemoteUser, IncomingMessage
from django_kepi.tasks import fetch
from things_for_testing import KepiTestCase
import logging
import httpretty
import json

logger = logging.getLogger(name='django_kepi')

POLLY_URL = 'https://remote.example.net/users/polly'
SUKI_URL = 'https://remote.example.net/services/suki/kettle'
PUT_THE_KETTLE_ON = "Let's put the kettle on"
SUKI_TAKE_IT_OFF = "Suki, take it off again"
RESULT_URL = 'https://localhost/async_result'

class TestTasks(TestCase):

    def _mock_remote_object(self,
            url,
            ftype = 'Object',
            content = '',
            status = 200):

        headers = {
                'Content-Type': 'application/activity+json',
                }

        httpretty.register_uri(
                httpretty.GET,
                url,
                status=status,
                headers=headers,
                body=bytes(content, encoding='UTF-8'))

        logger.debug('Mocking %s as %d: %s',
                url,
                status,
                content)

    def _mock_remote_service(self,
            url,
            ):

        def remote_service(request, uri, response_headers):

            self._sent_body = request.body.decode(encoding='ASCII')

            return [200, response_headers, 'Thank you.']

        self._sent_body = None

        httpretty.register_uri(
                httpretty.POST,
                url,
                body=remote_service)

    def _mock_local_endpoint(self):

        def local_endpoint(request, uri, response_headers):

            self._received_code = int(request.querystring['code'][0])
            self._received_url = request.querystring['url'][0]
            self._received_body = request.body.decode(encoding='ASCII')

            return [200, response_headers, '']

        self._received_code = None
        self._received_url = None
        self._received_body = None

        httpretty.register_uri(
                httpretty.POST,
                RESULT_URL,
                body=local_endpoint)


    @httpretty.activate
    def test_request_success(self):

        self._mock_remote_object(
            url = POLLY_URL,
            content = PUT_THE_KETTLE_ON,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = POLLY_URL,
                post_data = None,
                result_url = RESULT_URL,
                )

        self.assertEqual(self._received_code, 200)
        self.assertEqual(self._received_url, POLLY_URL)
        self.assertEqual(self._received_body, PUT_THE_KETTLE_ON)

    @httpretty.activate
    def test_request_failure(self):

        self._mock_remote_object(
            url = POLLY_URL,
            content = 'no idea, mate',
            status = 404,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = POLLY_URL,
                post_data = None,
                result_url = RESULT_URL,
                )

        self.assertEqual(self._received_code, 404)
        self.assertEqual(self._received_url, POLLY_URL)

    @httpretty.activate
    def test_request_gone(self):

        self._mock_remote_object(
            url = POLLY_URL,
            content = "they've all gone away",
            status = 410,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = POLLY_URL,
                post_data = None,
                result_url = RESULT_URL,
                )

        self.assertEqual(self._received_code, 410)
        self.assertEqual(self._received_url, POLLY_URL)

    @httpretty.activate
    def test_submit_success(self):

        self._mock_remote_service(
            url = SUKI_URL,
            )
        self._mock_local_endpoint()

        fetch(
                fetch_url = SUKI_URL,
                post_data = SUKI_TAKE_IT_OFF,
                result_url = None,
                )

        self.assertEqual(self._sent_body, SUKI_TAKE_IT_OFF)


