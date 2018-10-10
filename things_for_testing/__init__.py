from __future__ import absolute_import, unicode_literals
from .celery import app as celery_app
from django.test import TestCase
import httpretty
import logging

__all__ = ('celery_app',)

logger = logging.Logger('things_for_testing')

class KepiTestCase(TestCase):
    def _mock_remote_object(self,
            url,
            ftype = 'Object',
            fields = {},
            status = 200):

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

        logger.info('Mocking %s as %d: %s',
                url,
                status,
                fields)


