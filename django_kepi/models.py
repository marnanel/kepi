from django_kepi.activity_model import Activity
from django_kepi.something_model import ActivityModel

def new_activity_identifier():
    # we have to keep this in for now,
    # to pacify makemigrations
    return None

#######################

__all__ = [
        'Activity',
        'new_activity_identifier',
        'ActivityModel',
        ]
