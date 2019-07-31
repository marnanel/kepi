from . import thing
import logging

logger = logging.getLogger(name='django_kepi')

######################

# FIXME The activity_form for Activities should
# contain the whole activity_form in the 'object'
# field, not just the id (which might not be
# dereferencable anyway).

class Activity(thing.Thing):

    def go_into_outbox_if_local(self):

        from django_kepi.models.collection import Collection
        from django_kepi.find import find_local

        if not self.is_local:
            return

        actor = self['actor__obj']

        logger.info('%s: going into %s\'s outbox',
                self.number,
                actor.f_preferredUsername)

        outbox_url = actor['outbox']
        logger.debug('  -- which is %s', outbox_url)

        outbox = find_local(outbox_url,
                object_to_store=self)
