from django.db import models
from django_kepi import object_type_registry, find, register_type
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import django_kepi.tasks
import logging
import random
import json
import datetime
import warnings
import uuid

logger = logging.getLogger(name='django_kepi')

#######################

def new_activity_identifier():
    template = settings.KEPI['ACTIVITY_URL_FORMAT']
    slug = '%08x' % (random.randint(0, 0xffffffff),)
    return template % (slug,)

#######################

def _object_to_id_and_type(obj):
    """
    Takes an object passed in to Activity.create(),
    and returns a (url, type) pair to find it with
    lookup().
    
    "type" may be None if we can't determine a type,
    so lookup() will have to check everything.
    """

    # Is it a string?
    if isinstance(obj, str):
        return obj, None

    # Maybe it has an activity_id property.
    try:
        check_url = obj.activity_id

        try:
            check_type = obj.activity_type
        except AttributeError:
            check_type = None

        return check_url, check_type

    except AttributeError:
        pass # nope, try something else

    # Maybe it's a dict with 'id' and 'type' fields.
    try:
        check_url = obj['id']

        try:
            check_type = obj['type']
        except KeyError:
            check_type = None

        return check_url, check_type

    except KeyError:
        # So it *does* have fields, but "id" isn't
        # one of them. This breaks preconditions.
        raise ValueError('Explicit objects must have an id')

    except TypeError:
        pass # Can't subscript at all.

#######################

class Activity(models.Model):

    CREATE='C'
    UPDATE='U'
    PARTIAL_UPDATE='P'
    DELETE='D'
    FOLLOW='F'
    ADD='+'
    REMOVE='-'
    LIKE='L'
    UNDO='U'
    ACCEPT='A'
    REJECT='R'

    ACTIVITY_TYPE_CHOICES = (
            (CREATE, 'Create'),
            (UPDATE, 'Update'),
            (PARTIAL_UPDATE, 'p Update'),
            (DELETE, 'Delete'),
            (FOLLOW, 'Follow'),
            (ADD, 'Add'),
            (REMOVE, 'Remove'),
            (LIKE, 'Like'),
            (UNDO, 'Undo'),
            (ACCEPT, 'Accept'),
            (REJECT, 'Reject'),
            )

    f_type = models.CharField(
            max_length=1,
            choices=ACTIVITY_TYPE_CHOICES,
            )

    identifier = models.URLField(
            max_length=255,
            primary_key=True,
            default=new_activity_identifier,
            )

    f_actor = models.URLField(
            max_length=255,
            blank=True,
            )

    f_object_type = models.CharField(
            max_length=255,
            blank=True,
            )

    f_object = models.URLField(
            max_length=255,
            blank=True,
            )

    f_target = models.URLField(
            max_length=255,
            blank=True,
            )

    active = models.BooleanField(
            default=True,
            )

    pending = models.BooleanField(
            default=False,
            )

    source = models.CharField(
            max_length=255,
            null=True,
            default=None)

    # XXX Updates from clients are partial,
    # but updates from remote sites are total.
    # We don't currently let clients create Activities,
    # but if we ever do, we should flag which it was.

    def __str__(self):

        if self.active:
            inactive_warning = ''
        else:
            inactive_warning = ' INACTIVE'

        result = '[%s %s%s]' % (
                self.f_type,
                self.identifier,
                inactive_warning,
                )
        return result

    @property
    def activity_id(self):
        return self.identifier

    @property
    def activity_type(self):
        return self.f_type

    @property
    def activity_form(self):
        result = {
            'id': self.identifier,
            'type': self.get_f_type_display(),
            }

        for fieldname in ['actor', 'object', 'target']:

            value = getattr(self, 'f_'+fieldname)
            if value is not None:
                result[fieldname] = value

        return result

    TYPES = {
            #          actor  object  target
            'Create': (True,  True,   False),
            'Update': (True,  True,   False),
            'Delete': (True,  True,   False),
            'Follow': (True,  True,   False),
            'Add':    (True,  False,  True),
            'Remove': (True,  False,  True),
            'Like':   (True,  True,   False),
            'Undo':   (False, True,   False),
            'Accept': (True,  True,   False),
            'Reject': (True,  True,   False),
            }

    def send_notifications(self):
        recipients = set()

        if self.f_type=='Accept':
            # XXX This gets complicated;
            # f_object should have been resolved to an Activity by now!
            recipients.add(self.f_object)
        elif self.f_type=='Add':
            # This is used for pinning a status,
            # but that's not something we're supporting
            # in the first version.
            #
            # XXX When we *do* support it, this will
            # require checking that the actor has the
            # right to update that collection (but we'll
            # only support the "featured" collection
            # listed in their own profile), fetching
            # the listed status if we don't already have it,
            # and setting that to be the pinned status of
            # their account.
            pass
        elif self.f_type=='Announce':
            # XXX if f_object is remote,
            # ensure we have it, and fetch if not.
            # If f_object is local,
            # notify it.
            pass
        elif self.f_type=='Block':
            # Nobody gets notified about blocks
            pass
        elif self.f_type=='Create':
            # XXX this is very complicated
            pass
        elif self.f_type=='Delete':
            # XXX
            pass
        elif self.f_type=='Follow':
            # XXX if the user is one of ours, and they
            # auto-accept, and they're not already following...
            pass
        elif self.f_type=='Like':
            recipients.add(self.f_object)
        elif self.f_type=='Reject':
            # XXX This gets complicated;
            # f_object should have been resolved to an Activity by now!
            recipients.add(self.f_object)
        elif self.f_type=='Remove':
            # see comment for 'Add'
            pass
        elif self.f_type=='Undo':
            # XXX
            pass
        elif self.f_type=='Update':
            # XXX
            pass



        for recipient in recipients:
            recipient.activity_notified(self)

    @classmethod
    def register_all_activity_types(cls):
        for t in cls.TYPES.keys():
            register_type(t, cls)
        register_type('Activity', cls)

    @classmethod
    def activity_find(cls, url):
        logger.info('a_f %s', str(url))
        return cls.objects.get(identifier=url)

    @classmethod
    def activity_create(cls, fields):
        return cls.create(value, local=False)

    @classmethod
    def create(cls, value,
            sender=None):

        logger.debug('Creating Activity from %s', str(value))

        if 'type' not in value:
            raise ValueError("Activities must have a type")

        if 'id' not in value and sender is not None:
            raise ValueError("Remote activities must have an id")

        fields = {
                'active': True,
                }

        for f,v in value.items():
            fields['f_'+f] = v

        # XXX nasty temporary hack which will go away soon
        for name in ['f_to', 'f_cc']:
            if name in fields:
                del fields[name]

        try:
            need_actor, need_object, need_target = cls.TYPES[value['type']]
        except KeyError:
            raise ValueError('{} is not an Activity type'.format(value['type']))

        if need_actor!=('actor' in value) or \
                need_object!=('object' in value) or \
                need_target!=('target' in value):

                    def params(a, o, t):
                        result = []
                        if a: result.append('actor')
                        if o: result.append('object')
                        if t: result.append('target')

                        return '['+' '.join(result)+']'

                    we_have = params(
                            'actor' in value,
                            'object' in value,
                            'target' in value,
                            )

                    we_need = params(
                            need_actor,
                            need_object,
                            need_target,
                            )

                    raise ValueError('Wrong parameters for type {}: we have {}, we need {}'.format(
                        value['type'],
                        we_have, we_need))

        result = cls(**fields)
        result.save()
        result.send_notifications()

        return result

    # TODO: there should be a clean() method with the same
    # checks as create().

########################################

Activity.register_all_activity_types()
