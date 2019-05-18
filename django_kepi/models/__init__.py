from django_kepi.models.thing import Thing
from django_kepi.something_model import ActivityModel

def new_activity_identifier():
    # we have to keep this in for now,
    # to pacify makemigrations
    return None

#######################

__all__ = [
        'Thing',
        'new_activity_identifier',
        'ActivityModel',
        ]
