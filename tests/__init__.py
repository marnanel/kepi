from django_kepi.models import create

def _create_person(name,
        **kwargs):
    spec = {
        'name': name,
        'id': 'https://altair.example.com/users/'+name,
        'type': 'Person',
        }

    spec.update(kwargs)

    return create(spec)

