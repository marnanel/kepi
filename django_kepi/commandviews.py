import logging
from django_kepi.models.audience import Audience

logger = logging.getLogger(name='django_kepi')

class ObjectCommandView(object):

    def __init__(self, subject):
        logger.debug('%s created for %s',
                self.__class__.__name__,
                subject,
                )
        self.subject = subject

    def _items_inner(self,
            verbosity=0):
        s = self.subject

        result = {
                'is_local': s.is_local,
                'is_active': s.is_local,
                'url': s.url,
                'type': s.f_type,
                }

        result.update(
                Audience.get_audiences_for(s))

        return result

    def items(self, verbosity=0):
        """
        Returns a dict of items for this object.
        The field names will be prefixed with the
        object's identifier.

        "verbosity" is an integer between 0 and 3.
        The higher the verbosity, the more items
        will be included.
        """
        result = self._items_inner(
                verbosity = verbosity,
                )
        result = self._decorate_dict_with_short_id(result)

        logger.debug('%s for %s, verbosity %d, gives %s',
                self.__class__.__name__,
                self.subject,
                verbosity,
                result,
                )

        return result

    def _decorate_dict_with_short_id(self, d):
        short_id = self.subject.short_id
        result = dict([
            (short_id+'.'+f, v)
            for f, v
            in d.items()])

        return result

    @classmethod
    def commandline_names_to_activitypub(cls,
            names):

        logger.debug('No conversion needed between commandline names '+\
                'and ActivityPub: %s',
            names)

        return names

    @classmethod
    def _rename_dict_fields(
            cls,
            names,
            corrigenda,
            ):

        for acname, ourname in corrigenda:

            if acname in names:
                continue

            if ourname not in names:
                continue

            names[acname] = names[ourname]
            del names[ourname]

        return names

class ItemCommandView(ObjectCommandView):
    
    def _items_inner(self,
            verbosity=0):

        result = super()._items_inner(verbosity)
        s = self.subject

        for field in [
                'content',
                'attributedTo',
                ]:
            result[field] = s[field]

        for field in [
                'visibility',
                'thread',
                'conversation',
                'mentions',
                ]:
            result[field] = getattr(s, field)

        return result

class ActorCommandView(ObjectCommandView):
    
    _fields_to_rename = [
            ('preferredUsername', 'username'),
            ('summary', 'bio'),
            ]

    def _items_inner(self,
            verbosity=0,
            ):

        result = super()._items_inner(verbosity)
        s = self.subject

        for field in [
                'name',
                ]:
            result[field] = s[field]

        for acname, ourname in self._fields_to_rename:
            result[ourname] = s[acname]

        for field in [
                'auto_follow',
                ]:
            result[field] = getattr(s, field)

        for field in [
                'icon',
                'header',
                ]:
            v = s[field]
            if v is not None:
                v = v['url']

            result[field] = v

        return result

    @classmethod
    def commandline_names_to_activitypub(cls,
            names):

        names = cls._rename_dict_fields(
                names,
                cls._fields_to_rename,
                )

        return names

class ActivityCommandView(ObjectCommandView):
    pass

def view_class_for(cls):

    from django_kepi.models import AcObject, AcItem, AcActor, AcActivity

    if issubclass(cls, AcItem):
        return ItemCommandView
    elif issubclass(cls, AcActor):
        return ActorCommandView
    elif issubclass(cls, AcActivity):
        return ActivityCommandView
    elif issubclass(cls, AcObject):
        return ObjectCommandView
    else:
        logger.warn('Attempt to find a CommandView for '+\
                'non-ActivityPub type "%s"',
                cls.__name__)
        return None

def view_for(something):

    cls = view_class_for(something.__class__)

    if cls is None:
        return None

    return cls(something)
