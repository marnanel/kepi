from django.db import models, IntegrityError
from django.conf import settings
from polymorphic.models import PolymorphicModel
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.mention import Mention
import django_kepi.side_effects as side_effects
import logging
import random
import json
import datetime
import warnings
from django_kepi.types import ACTIVITYPUB_TYPES

logger = logging.getLogger(name='django_kepi')

######################

ACTIVITY_TYPES = sorted(ACTIVITYPUB_TYPES.keys())

ACTIVITY_TYPE_CHOICES = [(x,x) for x in ACTIVITY_TYPES]

def _new_number():
    return '%08x' % (random.randint(0, 0xffffffff),)

######################

class Thing(PolymorphicModel):

    number = models.CharField(
            max_length=8,
            primary_key=True,
            unique=True,
            default=_new_number,
            )

    f_type = models.CharField(
            max_length=255,
            choices=ACTIVITY_TYPE_CHOICES,
            )

    f_actor = models.CharField(
            max_length=255,
            default=None,
            null=True,
            blank=True,
            )

    remote_url = models.URLField(
            max_length=255,
            unique=True,
            null=True,
            blank=True,
            default=None,
            )

    active = models.BooleanField(
            default=True,
            )

    other_fields = models.TextField(
            blank=True,
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

            if 'raw' not in name_parts:
                if result:
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
            others = {}

            if self.other_fields:
                try:
                    others = json.loads(self.other_fields)
                except json.JSONDecodeError:
                    logger.warn('%s: other_fields contained non-JSON: %s.' + \
                            'Discarding.',
                        self.number,
                        self.other_fields)

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

    def run_side_effects(self):

        from django_kepi.find import find
        from django_kepi.delivery import deliver

        f_type = json.loads(self.f_type).lower()

        if not hasattr(side_effects, f_type):
            logger.debug('  -- no side effects for %s',
                    f_type)
            return

        result = getattr(side_effects, f_type)(self)

        if result==False:
            logger.debug('  -- deleting original object')
            logger.info(' --> This is %s %s',
                    self, self.thing_ptr_id)
            try:
                self.delete()
            except AssertionError:
                logger.info('    -- deletion failed, probably because of '+\
                        'https://code.djangoproject.com/ticket/23076')

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

        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            self.number = _new_number()
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


