from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

app = Celery('things_for_testing',
        broker='amqp://localhost')

app.config_from_object('django.conf:settings')

app.autodiscover_tasks(packages=['django_kepi'])

app.config_from_object('django.conf:settings')
def debug_task(self):
        print('Request: {0!r}'.format(self.request))
