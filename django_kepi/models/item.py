from django.db import models
from . import thing
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Item(thing.Thing):

    @property
    def visibility(self):
        audiences = django_kepi.models.audience.Audience.get_audiences_for(self)
        logger.debug('%s', str(audiences))

        if django_kepi.models.audience.PUBLIC in audiences.get('to', []):
            return 'public'
        elif django_kepi.models.audience.PUBLIC in audiences.get('cc', []):
            return 'unlisted'
        return 'direct'

    @property
    def text(self):
        return self['content']
