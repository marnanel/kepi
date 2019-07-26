from . import thing
import logging

logger = logging.getLogger(name='django_kepi')

######################

# FIXME The activity_form for Activities should
# contain the whole activity_form in the 'object'
# field, not just the id (which might not be
# dereferencable anyway).

class Activity(thing.Thing):
    pass
