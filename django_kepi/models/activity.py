from . import thing
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Activity(thing.Object):

    _explicit_object_field = False

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

    @property
    def activity_form(self):
        result = super().activity_form

        if not self._explicit_object_field:
            return result

        our_object = self['object__obj']

        if our_object is None:
            logger.warn('%s: object of action (%s) is not known!',
                    self, result['object'])
        else:
            result['object'] = our_object.activity_form

        return result

##############################

class Create(Activity):
    _explicit_object_field = True

class Update(Activity):
    pass

class Delete(Activity):
    pass

class Follow(Activity):
    _explicit_object_field = True

class Add(Activity):
    pass

class Remove(Activity):
    pass

class Like(Activity):
    pass

class Undo(Activity):
    pass

class Accept(Activity):
    _explicit_object_field = True

class Reject(Activity):
    pass

class Announce(Activity):
    # aka "boost"
    pass
