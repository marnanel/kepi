from django.db import models, IntegrityError
from django.conf import settings
from django_kepi.find import find, is_local
from django_kepi.delivery import deliver
import django_kepi.models.following
import django_kepi.models.audience
import logging
import random
import json
import datetime
import warnings

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

ACTIVITY_TYPE_CHOICES = [(x,x) for x in sorted(ACTIVITY_TYPES)]

OTHER_OBJECT_TYPES = set([
    # https://www.w3.org/TR/activitystreams-vocabulary/

    'Actor', 'Application', 'Group', 'Organization', 'Person', 'Service',

    'Article', 'Audio', 'Document', 'Event', 'Image', 'Note', 'Page',
    'Place', 'Profile', 'Relationship', 'Video',

    ])

######################

class Thing(models.Model):

    number = models.CharField(
            max_length=8,
            primary_key=True,
            unique=True,
            default='',
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

    f_name = models.CharField(
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

        return settings.KEPI['ACTIVITY_URL_FORMAT'] % (self.number,)

    def __str__(self):

        if self.active:
            inactive_warning = ''
        else:
            inactive_warning = ' INACTIVE'

        if self.f_name:
            details = self.f_name
        else:
            details = self.url

        result = '[%s %s %s%s]' % (
                self.number,
                self.f_type,
                details,
                inactive_warning,
                )
        return result

    @property
    def activity_type(self):
        return self.f_type

    @property
    def activity_form(self):
        result = {
            'id': self.url,
            'type': self.get_f_type_display(),
            }

        for fieldname in ['actor', 'name']:

            value = getattr(self, 'f_'+fieldname)
            if value:
                result[fieldname] = value

        for f in ThingField.objects.filter(parent=self):
            result[f.name] = json.loads(f.value)

        return result

    def __contains__(self, name):
        try:
            self.__getitem__(name)
            return True
        except:
            return False

    def __getitem__(self, name):

        name_parts = name.split('__')
        name = name_parts.pop(0)

        if name=='name':
            result = self.f_name
        elif name=='actor':
            result = self.f_actor
        elif name=='type':
            result = self.f_type
        else:
            field = ThingField.objects.get(
                    parent = self,
                    name = name,
                    )

            result = field.value

            if 'raw' not in name_parts:
                result = json.loads(result)

        if 'obj' in name_parts:
            result = find(result,
                    local_only=True)

        return result

    def send_notifications(self):
        if self.f_type=='Accept':
            obj = self['object__obj']

            if obj['type']!='Follow':
                logger.warn('Object %s was Accepted, but it isn\'t a Follow',
                    obj)
                return

            logger.debug(' -- follow accepted')

            django_kepi.models.following.accept(
                    follower = obj['actor'],
                    following = self['actor'],
                    )

        elif self.f_type=='Follow':

            local_user = find(self['object'], local_only=True)
            remote_user = find(self['actor'])

            if local_user is not None and local_user.auto_follow:
                logger.info('Local user %s has auto_follow set; must Accept',
                        local_user)
                django_kepi.models.following.accept(
                        follower = self['actor'],
                        following = self['object'],
                        # XXX this causes a warning; add param to disable it
                        )

                accept_the_request = create(
                    f_to = remote_user['inbox'],
                    f_type = 'Accept',
                    f_actor = self['object'],
                    f_object = self.url,
                    run_side_effects = False,
                    )

                deliver(accept_the_request.number)

            else:
                django_kepi.models.following.request(
                        follower = self['actor'],
                        following = self['object'],
                        )

        elif self.f_type=='Reject':
            obj = self['object__obj']

            if obj['type']!='Follow':
                logger.warn('Object %s was Rejected, but it isn\'t a Follow',
                    obj)
                return

            logger.debug(' -- follow rejected')

            django_kepi.models.following.reject(
                    follower = obj['actor'],
                    following = self['actor'],
                    )

    @property
    def is_local(self):
        if not self.remote_url:
            return True

        return is_local(self.remote_url)

    def entomb(self):
        logger.info('%s: entombing', self)

        if self.f_type=='Tombstone':
            logger.warn('   -- already entombed; ignoring')
            return

        if not self.is_local:
            raise ValueError("%s: you can't entomb remote things %s",
                    self, str(self.remote_url))

        former_type = self.f_type

        self.f_type = 'Tombstone'
        self.active = True

        ThingField.objects.filter(parent=self).delete()

        for f,v in [
                ('former_type', former_type),
                # XXX 'deleted', when we're doing timestamps
                ]:
            ThingField(parent=self, name=f, value=json.dumps(v)).save()

        self.save()
        logger.info('%s: entombing finished', self)

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
    def create(cls,
            sender=None,
            run_side_effects=True,
            **value):

        # Remove the "f_" prefix, which exists so that we can write
        # things like f_type or f_object without using reserved keywords.
        for k,v in value.copy().items():
            if k.startswith('f_'):
                value[k[2:]] = v
                del value[k]

        # Now, let's fix the types of keys and values.

        for k,v in value.copy().items():
            if not isinstance(k, str):
                raise ValueError('Things can only have keys which are strings: %s',
                        str(k))

            if isinstance(v, str):
                continue # strings are fine
            elif isinstance(v, dict):
                continue # so are dicts
            elif isinstance(v, bool):
                continue # also booleans
            elif isinstance(v, list):
                continue # and lists as well
            elif isinstance(v, Thing):
                value[k] = v.url
                continue

            try:
                value[k] = v.activity_form
                logger.debug('  -- fixed type: %s=%s',
                        k, value[k])
            except AttributeError:
                value[k] = str(v)
                logger.debug('  -- fixed type to string: %s=%s',
                        k, value[k])

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

        # Right, we need to create some objects.
        # Everything in "value" needs to go into:
        #    - a Thing, containing records such as "type",
        #    - zero or more Audiences, for "to" etc
        #    - zero or more ThingFields, for everything else

        for f,v in value.items():
            if f in [
                    'actor',
                    'name',
                    'type',
                    ]:
                record_fields['f_'+f] = v
                del other_fields[f]

        if 'id' in value:
            record_fields['remote_url'] = value['id']

        for f in ['id', 'type', 'actor', 'name']:
            if f in other_fields:
                del other_fields[f]

        result = cls(**record_fields)
        result.save()
        logger.debug('Created %s (%s): ----',
                result.f_type,
                result.f_name,
                )

        for f, v in other_fields.items():

            if f in django_kepi.models.audience.AUDIENCE_FIELD_NAMES:
                django_kepi.models.audience.Audience.add_audiences_for(
                    thing = result,
                    field = f,
                    value = v,
                    )
            else:
                value = json.dumps(v, sort_keys=True)
                n = ThingField(
                        parent = result,
                        name = f,
                        value = value,
                        )
                n.save()
                logger.debug('  -- %s', n)

        for f,v in [
                ('actor', result.f_actor),
                ('url', result.url),
                ]:
            if v:
                logger.debug('  -- [%s %12s %s]',
                        result.number, f, v)

        if run_side_effects:
            result.send_notifications()

        return result

    def save(self, *args, **kwargs):

        we_are_new = self.pk is None

        if not self.number:
            self.number = '%08x' % (random.randint(0, 0xffffffff),)

        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            self.number = None
            return self.save(*args, **kwargs)

        if we_are_new and self.f_type in OTHER_OBJECT_TYPES:
            # XXX we shouldn't do this unless it came in via an outbox!
            logger.debug('New Thing is not an activity: %s',
                    str(self.activity_form))
            logger.debug('We must create a Create wrapper for it.')

            wrapper = Thing.create(
                f_type = 'Create',
                f_actor = self.activity_actor,
                to = self.activity_to,
                cc = self.activity_cc,
                f_object = self.activity_id,
                )

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
    # all others go here.
    name = models.CharField(
            max_length=255,
            )

    # Stored in JSON.
    value = models.TextField(
        )

    def __str__(self):
        return '[%s %12s %s]' % (
                self.parent.number,
                self.name,
                self.value)

########################################

def create(*args, **kwargs):
    return Thing.create(*args, **kwargs)

