from django.db import models
from . import acobject
import logging

logger = logging.getLogger(name='kepi')

######################

class AcActivity(acobject.AcObject):

    _explicit_object_field = False

    f_actor = models.CharField(
            max_length=255,
            default=None,
            null=True,
            blank=True,
            )

    f_object = models.CharField(
            max_length=255,
            default=None,
            null=True,
            blank=True,
            )

    class Meta:
        verbose_name = 'activity'
        verbose_name_plural = 'activities'

    def go_into_outbox_if_local(self):

        from kepi.bowler_pub.models.collection import Collection
        from kepi.bowler_pub.find import find

        if not self.is_local:
            return

        actor = self['actor__find']

        logger.info('%s: going into %s\'s outbox',
                self.id,
                actor.id)

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

class AcCreate(AcActivity):
    _explicit_object_field = True

    def __str__(self):
        return '(%s) create of %s' % (
                self.id,
                self['object'],
                )

class AcUpdate(AcActivity):
    pass

class AcDelete(AcActivity):
    pass

class AcFollow(AcActivity):
    def __str__(self):

        return '(%s) request that %s follow %s' % (
                self.id,
                self['actor'],
                self['object'],
                )

class AcAdd(AcActivity):
    pass

class AcRemove(AcActivity):
    pass

class AcLike(AcActivity):
    pass

class AcUndo(AcActivity):
    pass

class AcAccept(AcActivity):
    _explicit_object_field = True

    def __str__(self):

        return '(%s) accept %s' % (
                self.id,
                self['object__obj'].__str__(),
                )

class AcReject(AcActivity):
    def __str__(self):

        return '(%s) reject %s' % (
                self.id,
                self['object__obj'].__str__(),
                )

class AcAnnounce(AcActivity):
    # aka "boost"
    pass
