from django_kepi.models import create

def _create_person(name):
    return create({
        'name': name,
        'id': 'https://altair.example.com/users/'+name,
        'type': 'Person',
        })

