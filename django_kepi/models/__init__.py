from django_kepi.models.thing import Thing, create

def new_activity_identifier():
    # we have to keep this in for now,
    # to pacify makemigrations
    return None

#######################

__all__ = [
        'Thing',
        'create',
        'new_activity_identifier',
        ]
