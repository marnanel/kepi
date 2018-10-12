from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app
from django.test import TestCase
from django_kepi import logger
import httpretty
import logging

class KepiTestCase(TestCase):

    def _mock_remote_object(self,
            url,
            ftype = 'Object',
            fields = None,
            status = 200):

        if fields is None:
            fields = {}

        if 'id' not in fields:
            fields['id'] = url

        if 'type' not in fields:
            fields['type'] = ftype

        headers = {
                'Content-Type': 'application/activity+json',
                }

        httpretty.register_uri(
                httpretty.GET,
                url,
                status=status,
                headers=headers,
                body=bytes(str(fields), encoding='UTF-8'))

        logger.debug('Mocking %s as %d: %s',
                url,
                status,
                fields)

        # For some reason, this allows Celery to
        # access /async_result in the test version;
        # without it, the socket library throws an error.
        httpretty.register_uri(
                httpretty.POST,
                'https://localhost/async_result',
                body='something')


