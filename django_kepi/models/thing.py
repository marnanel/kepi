from django.db import models, IntegrityError
from django.conf import settings
from polymorphic.models import PolymorphicModel
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.mention import Mention
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

class Thing(PolymorphicModel):

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

    other_fields = models.TextField(
            default='',
            )

    @property
    def url(self):
        if self.remote_url is not None:
            return self.remote_url

        return settings.KEPI['ACTIVITY_URL_FORMAT'] % (self.number,)

    @property
    def id(self):
        return self.url

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
    def pretty(self):
        result = ''
        curly = '{'

        items = [
                ('type', self.f_type),
                ]

        if not self.active:
            items.append( ('_active', False) )

        for f, v in sorted(self.activity_form.items()):

            if f in ['type']:
                continue

            items.append( (f,v) )

        items.extend( [
                ('actor', self.f_actor),
                ('_name', self.f_name),
                ('_number', self.number),
                ('_remote_url', self.remote_url),
                ] )

        for f, v in items:

            if not v:
                continue

            if result:
                result += ',\n'

            result += '%1s %15s: %s' % (
                    curly,
                    json.dumps(f),
                    json.dumps(v),
                    )
            curly = ''

        result += ' }'

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

        for name in dir(self):
            if not name.startswith('f_'):
                continue

            value = getattr(self, name)

            if not isinstance(value, str):
                continue

            if value=='':
                value = None
            else:
                value = json.loads(value)

            result[name[2:]] = value

        if self.other_fields:
            result.update(json.loads(self.other_fields))

        result.update(Audience.get_audiences_for(self))

        return result

    def __contains__(self, name):
        try:
            self.__getitem__(name)
            return True
        except:
            return False

    def __getitem__(self, name):

        from django_kepi.find import find

        name_parts = name.split('__')
        name = name_parts.pop(0)

        if hasattr(self, 'f_'+name):
            result = getattr(self, 'f_'+name)

            if 'raw' not in name_parts and result is not None:
                result = json.loads(result)

        elif name in AUDIENCE_FIELD_NAMES:
            try:
                result = Audience.objects.filter(
                        parent = self,
                        field = AUDIENCE_FIELD_NAMES[name],
                        )
            except Audience.DoesNotExist:
                result = None
        else:
            others = json.loads(self.other_fields)
            if name in others:
                result = others[name]
            else:
                result = None

        if 'obj' in name_parts and result is not None:
            result = find(result,
                    local_only=True)

        return result

    def __setitem__(self, name, value):

        value = _normalise_type_for_thing(value)

        logger.debug('  -- %8s %12s %s',
                self.number,
                name,
                value,
                )

        if hasattr(self, 'f_'+name):
            setattr(self, 'f_'+name, json.dumps(value))
        elif name in AUDIENCE_FIELD_NAMES:

            if self.pk is None:
                # We *must* save at this point;
                # otherwise Audience might have no foreign key.
                self.save()

            Audience.add_audiences_for(
                    thing = self,
                    field = name,
                    value = value,
                    )
        else:
            others_json = self.other_fields
            if others_json:
                others = json.loads(others_json)
            else:
                others = {}

            others[name] = value
            self.other_fields = json.dumps(others)

        # Special-cased side effects:

        if name=='tag':

            # We must save, in order for Mention's fk to point to us
            self.save()

            Mention.set_from_tags(
                    status=self,
                    tags=value,
                    )

    def send_notifications(self):

        from django_kepi.find import find
        from django_kepi.delivery import deliver

        f_type = json.loads(self.f_type)

        if f_type=='Accept':
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

        elif f_type=='Follow':

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

                from django_kepi.create import create
                accept_the_request = create(
                        f_to = remote_user.url,
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

        elif f_type=='Reject':
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

        elif f_type=='Create':

            from django_kepi.create import create

            raw_material = dict([('f_'+f, v)
                for f,v in self['object'].items()])

            raw_material['attributedTo'] = self['actor']
            # XXX and also copy audiences, per
            # https://www.w3.org/TR/activitypub/ 6.2

            creation = create(**raw_material,
                    is_local = self.is_local,
                    run_side_effects = False)
            self['object'] = creation
            self.save()

        elif f_type in OTHER_OBJECT_TYPES:
            # XXX only if this came in via a local inbox
            logger.debug('New Thing is not an activity: %s',
                    str(self.activity_form))
            logger.debug('We must create a Create wrapper for it.')

            from django_kepi.create import create
            wrapper = create(
                f_type = 'Create',
                f_actor = self.f_actor,
                to = self['to'],
                cc = self['cc'],
                f_object = self.url,
                run_side_effects = False,
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

    @property
    def is_local(self):

        from django_kepi.find import is_local

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

    def save(self, *args, **kwargs):

        if not self.number:
            self.number = '%08x' % (random.randint(0, 0xffffffff),)

        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            self.number = None
            return self.save(*args, **kwargs)

######################################

def _normalise_type_for_thing(v):
    if v is None:
        return v # we're good with nulls
    if isinstance(v, str):
        return v # strings are fine
    elif isinstance(v, dict):
        return v # so are dicts
    elif isinstance(v, bool):
        return v # also booleans
    elif isinstance(v, list):
        return v # and lists as well
    elif isinstance(v, Thing):
        return v.url # Things can deal with themselves

    # okay, it's something weird

    try:
        return v.activity_form
    except AttributeError:
        return str(v)
