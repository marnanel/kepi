from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app
from django.test import TestCase
import httpretty
import logging

logger = logging.getLogger(name='things_for_testing')

class KepiTestCase(TestCase):

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

        # For some reason, this allows Celery to
        # access /async_result in the test version;
        # without it, the socket library throws an error.
        httpretty.register_uri(
                httpretty.POST,
                'https://localhost/async_result',
                body='something')


