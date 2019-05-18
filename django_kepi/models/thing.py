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

OTHER_OBJECT_TYPES = set([
    # https://www.w3.org/TR/activitystreams-vocabulary/

    'Actor', 'Application', 'Group', 'Organization', 'Person', 'Service',

    'Article', 'Audio', 'Document', 'Event', 'Image', 'Note', 'Page',
    'Place', 'Profile', 'Relationship', 'Video',

    ])

class Thing(models.Model):

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

    active = models.BooleanField(
            default=True,
            )

    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return settings.KEPI['ACTIVITY_URL_FORMAT'] % (self.uuid,)

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

        for f in ThingFields.objects.filter(parent=self):
            result[f.name] = json.loads(f.value)

        return result

    def send_notifications(self):
        pass # XXX not yet implemented

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

    @classmethod
    def create(cls, value,
            sender=None,
            run_side_effects=True):

        logger.debug('Creating thing from %s', str(value))

        if 'type' not in value:
            raise ValueError("Things must have a type")

        value['type'] = value['type'].title()

        if 'id' not in value and sender is not None:
            raise ValueError("Remote things must have an id")

        record_fields = {
                'active': True,
                }
        other_fields = value.copy()

        try:
            need_actor, need_object, need_target = cls.TYPES[value['type']]
        except KeyError:
            if value['type'] in OTHER_OBJECT_TYPES:
                logger.debug('Thing type %s is known, but not an Activity',
                        value['type'])

                need_actor = need_object = need_target = False
            else:
                logger.debug('Unknown thing type: %s', value['type'])
                raise ValueError('{} is not a thing type'.format(value['type']))

            # XXX We don't currently allow people to create Tombstones here,
            # but we should.

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

                    message = 'Wrong parameters for thing type {}: we have {}, we need {}'.format(
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

        for f in ['id', 'type', 'actor']:
            if f in other_fields:
                del other_fields[f]

        logger.debug('About to create thing with fields: %s', record_fields)

        result = cls(**record_fields)
        result.save()
        logger.debug('Thing created: %s', result)

        for f, v in other_fields.items():
            n = ThingField(
                    parent = result,
                    name = f,
                    value = json.dumps(v, sort_keys=True),
                    )
            n.save()
            logger.debug('ThingField created: %s', n)

        if run_side_effects:
            result.send_notifications()

        return result

    # TODO: there should be a clean() method with the same
    # checks as create().

    def save(self, *args, **kwargs):

        we_are_new = self.pk is None

        super().save(*args, **kwargs)

        if we_are_new and self.f_type in OTHER_OBJECT_TYPES:
            logger.debug('New Thing is not an activity: %s',
                    str(self.activity_form))
            logger.debug('We must create a Create wrapper for it.')

            wrapper = Thing.create({
                'type': 'Create',
                'actor': self.activity_actor,
                'to': self.activity_to,
                'cc': self.activity_cc,
                'object': self.activity_id,
                })

            wrapper.save()
            logger.debug('Created wrapper %s',
                    str(wrapper.activity_form))

            # XXX We copy "to" and "cc" per
            # https://www.w3.org/TR/activitypub/#object-without-create
            # which also requires us to copy
            # the two blind versions, and "audience".
            # We don't support those (atm), but
            # we should probably copy them anyway.

########################################

class ThingField(models.Model):

    class Meta:
        unique_together = ['parent', 'name']

    parent = models.ForeignKey(
            Thing,
            on_delete=models.CASCADE,
            )

    # "type" and "actor" are fields in the Thing model itself;
    # all ohers go here.
    name = models.CharField(
            max_length=255,
            )

    # Stored in JSON.
    value = models.TextField(
        )

    def __str__(self):
        return '%s.%s = %s' % (
                self.parent.uuid,
                self.name,
                self.value)

########################################

def create(*args, **kwargs):
    return Thing.create(*args, **kwargs)
