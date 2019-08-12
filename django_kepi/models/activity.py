from . import thing
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Activity(thing.Object):

    def go_into_outbox_if_local(self):

        from django_kepi.models.collection import Collection
        from django_kepi.find import find

        if not self.is_local:
            return

        actor = self['actor__obj']

        logger.info('%s: going into %s\'s outbox',
                self.number,
                actor.f_preferredUsername)

        outbox_url = actor['outbox']
        logger.debug('  -- which is %s', outbox_url)

        outbox = find(outbox_url,
                local_only=True,
                object_to_store=self)

##############################

class Create(Activity):

    @property
    def activity_form(self):
        result = super().activity_form

        result['object'] = self['object__obj'].activity_form

        return result

class Update(Activity):
    pass

class Delete(Activity):
    pass

class Follow(Activity):
    pass

class Add(Activity):
    pass

class Remove(Activity):
    pass

class Like(Activity):
    pass

class Undo(Activity):
    pass

class Accept(Activity):
    pass

class Reject(Activity):
    pass

class Announce(Activity):
    # aka "boost"
    pass
