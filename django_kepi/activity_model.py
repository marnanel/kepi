from django.db import models
from django_kepi import object_type_registry, find, register_type
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import logging
import random
import json
import datetime
import warnings
import uuid

logger = logging.getLogger(name='django_kepi')

######################

ACTIVITY_TYPES = set([
            'Create',
            'Update',
            'Delete',
            'Follow',
            'Add',
            'Remove',
            'Like',
            'Undo',
            'Accept',
            'Reject',
        ])

ACTIVITY_TYPE_CHOICES = [(x,x) for x in ACTIVITY_TYPES]

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

    uuid = models.UUIDField(
            default=uuid.uuid4,
            primary_key=True,
            )

    f_type = models.CharField(
            max_length=255,
            choices=ACTIVITY_TYPE_CHOICES,
            )

    remote_url = models.URLField(
            max_length=255,
            unique=True,
            null=True,
            default=None,
            )

    f_actor = models.URLField(
            max_length=255,
            blank=True,
            )

    other_fields = models.TextField(
            )

    active = models.BooleanField(
            default=True,
            )

    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return settings.KEPI['ACTIVITY_URL_FORMAT'] % (self.uuid,)

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
                self.url,
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
            'id': self.url,
            'type': self.get_f_type_display(),
            }

        for fieldname in ['actor']:

            value = getattr(self, 'f_'+fieldname)
            if value is not None:
                result[fieldname] = value

        for f,v in json.loads(self.other_fields).items():
            result[f] = v

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
            sender=None,
            run_side_effects=True):

        logger.debug('Creating Activity from %s', str(value))

        if 'type' not in value:
            raise ValueError("Activities must have a type")

        value['type'] = value['type'].title()

        if 'id' not in value and sender is not None:
            raise ValueError("Remote activities must have an id")

        record_fields = {
                'active': True,
                }
        other_fields = value.copy()

        try:
            need_actor, need_object, need_target = cls.TYPES[value['type']]
        except KeyError:
            logger.debug('Unknown Activity type: %s', value['type'])
            raise ValueError('{} is not an Activity type'.format(value['type']))

        if need_actor!=('actor' in value) or \
                need_object!=('object' in value) or \
                need_target!=('target' in value):

                    def params(a, o, t):
                        result = []
                        if a: result.append('actor')
                        if o: result.append('object')
                        if t: result.append('target')

                        if not result:
                            return 'none'

                        return '+'.join(result)

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

                    message = 'Wrong parameters for Activity type {}: we have {}, we need {}'.format(
                        value['type'], we_have, we_need)
                    logger.warn(message)
                    raise ValueError(message)

        for f,v in value.items():
            if f in [
                    'actor'
                    ]:
                record_fields['f_'+f] = v
                del other_fields[f]

        record_fields['f_type'] = value['type']

        if 'id' in value:
            # FIXME this allows people to create "remote" Activities
            # with local URLs, which is weird and shouldn't happen.
            record_fields['remote_url'] = value['id']

        for f in ['id', 'type']:
            if f in other_fields:
                del other_fields[f]

        record_fields['other_fields'] = json.dumps(
                other_fields,
                sort_keys=True,
                )

        logger.debug('About to create Activity with fields: %s', record_fields)

        result = cls(**record_fields)
        result.save()
        logger.debug('Activity created: %s', record_fields)

        if run_side_effects:
            result.send_notifications()

        return result

    # TODO: there should be a clean() method with the same
    # checks as create().

########################################

Activity.register_all_activity_types()
