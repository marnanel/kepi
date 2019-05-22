from django_kepi.models import create
import httpretty
import logging

logger = logging.getLogger(name='django_kepi')

def _create_person(name,
        **kwargs):
    spec = {
        'name': name,
        'id': 'https://altair.example.com/users/'+name,
        'type': 'Person',
        }

    spec.update(kwargs)

    return create(spec)

def _mock_remote_object(
        url,
        ftype = 'Object',
        content = '',
        status = 200,
        ):

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
