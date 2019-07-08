from django.db import models
from . import thing, audience
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Item(thing.Thing):

    f_content = models.CharField(
            max_length=255,
            blank=True,
            )

    f_attributedTo = models.CharField(
            max_length=255,
            blank=True,
            )

    @property
    def visibility(self):
        audiences = audience.Audience.get_audiences_for(self)
        logger.debug('%s', str(audiences))

        if audience.PUBLIC in audiences.get('to', []):
            return 'public'
        elif audience.PUBLIC in audiences.get('cc', []):
            return 'unlisted'
        return 'direct'

    @property
    def text(self):
        return self['content']
