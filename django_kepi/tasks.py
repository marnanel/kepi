from __future__ import absolute_import, unicode_literals
from celery import shared_task
import requests
import logging

logger = logging.getLogger('django_kepi.tasks')

@shared_task
def fetch(
        fetch_url,
        post_data,
        result_url,
        result_id,
        ):

    if post_data is None:
        logger.info('%s: GET', fetch_url)

        fetch = requests.get(fetch_url)
    else:
        logger.info('%s: POST', url)
        logger.debug('%s: with form data: %s',
                fetch_url, post_data)

        fetch = requests.post(fetch_url,
                data=post_data)

    logger.info('%s: response code was %d',
            fetch_url, fetch.status_code)
    logger.debug('%s: body was: %s',
            fetch_url, fetch.text)

    if result_url is not None:
        logger.info('%s: notifying %s',
            fetch_url, result_url)

        response = requests.post(
                result_url,
                params={
                    'success': fetch.status_code==200,
                    'uuid': result_id,
                    },
                data=fetch.text,
                )

        if response.status_code!=200:
            logger.warn('%s: notifying %s FAILED with code %d',
                    fetch_url, result_url, response.status_code)
        else:
            logger.info('%s: notification received okay',
                    fetch_url)
