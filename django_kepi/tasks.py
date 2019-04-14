from __future__ import absolute_import, unicode_literals
from celery import shared_task
import requests
import logging

logger = logging.getLogger(name='django_kepi')

@shared_task()
def fetch(
        fetch_url,
        post_data,
        result_url,
        ):

    if post_data is None:
        logger.info('batch %s: GET', fetch_url)

        fetch = requests.get(fetch_url)
    else:
        logger.info('batch %s: POST with form data: %s',
                fetch_url, post_data)

        fetch = requests.post(fetch_url,
                data=post_data)

    logger.info('batch %s: response code was %d, body was %s',
            fetch_url, fetch.status_code, fetch.text)

    if result_url is not None:

        response = requests.post(
                result_url,
                params={
                    'code': int(fetch.status_code),
                    'url': fetch_url,
                    },
                data=fetch.text,
                )

        if response.status_code!=200:
            logger.warn('batch %s: notifying %s FAILED with code %d',
                    fetch_url, result_url, response.status_code)
