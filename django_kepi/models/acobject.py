from django.db import models, IntegrityError
from django.conf import settings
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager
from django_kepi.models.audience import Audience, AUDIENCE_FIELD_NAMES
from django_kepi.models.thingfield import ThingField
from django_kepi.models.mention import Mention
from .. import ATSIGN_CONTEXT
import django_kepi.side_effects as side_effects
import logging
import random
import json
import warnings

logger = logging.getLogger(name='django_kepi')

######################

def _new_number():
    return '/%08x' % (random.randint(0, 0xffffffff),)

######################

class KepiManager(PolymorphicManager):

    # TODO: This should allow filtering on names
    # without their f_... prefixes, and also
    # transparently on ThingFields.

    def filter_local_only(self, *args, **kwargs):
        self._adjust_kwargs_for_local_only(kwargs)
        return self.filter(*args, **kwargs)

    def get_local_only(self, *args, **kwargs):
        self._adjust_kwargs_for_local_only(kwargs)
        return self.get(*args, **kwargs)

    def _adjust_kwargs_for_local_only(self, kwargs):

        LOCAL_ONLY = 'id__startswith'

        if LOCAL_ONLY in kwargs:
            raise ValueError(('%s is already an argument; '+\
                    'this should never happen') % (LOCAL_ONLY,))
        kwargs[LOCAL_ONLY] = '/'

######################

class AcObject(PolymorphicModel):

    id = models.CharField(
            max_length=255,
            primary_key=True,
            unique=True,
            blank=False,
            default=_new_number,
            editable=False,
            )

    objects = KepiManager()

    published = models.DateTimeField(
            default = timezone.now,
            editable = False,
            )

    @property
    def url(self):
        if self.id.startswith('/'):
            return settings.KEPI['ACTIVITY_URL_FORMAT'] % {
                    'number': self.id[1:],
                    'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                    }
        else:
            return self.id

    @property
    def number(self):
        if self.id.startswith('/'):
            return self.id[1:]
        else:
            return None

    def __str__(self):

        if self.is_local:
            details = '(%s)' % (self.id[1:],)
        else:
            details = self.id

        result = '[%s %s]' % (
                details,
                self.f_type,
                )
        return result

    @property
    def short_id(self):
        return self.id

    @property
    def pretty(self):
        result = ''
        curly = '{'

        items = [
                ('type', self.f_type),
                ]

        for f, v in sorted(self.activity_form.items()):

            if f in ['type']:
                continue

            items.append( (f,v) )

        items.extend( [
                ('actor', self.f_actor),
                ] )

        for f, v in items:

            if not v:
                continue

            if result:
                result += ',\n'

            result += '%1s %15s: %s' % (
                    curly,
                    f,
                    v,
                    )
            curly = ''

        result += ' }'

        return result

    @property
    def f_type(self):
        return self.__class__.__name__[2:]

    @property
    def activity_form(self):
        result = {
            '@context': ATSIGN_CONTEXT,
            'id': self.url,
            'type': self.f_type,
            'published': self.published,
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

        result.update(ThingField.get_fields_for(self))
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
        elif name in AUDIENCE_FIELD_NAMES:
            try:
                result = Audience.objects.filter(
                        parent = self,
                        field = AUDIENCE_FIELD_NAMES[name],
                        )
            except Audience.DoesNotExist:
                result = None
        else:
            try:
                another = ThingField.objects.get(
                        parent = self,
                        field = name)

                if 'raw' in name_parts:
                    result = another.value
                else:
                    result = another.interpreted_value

            except ThingField.DoesNotExist:
                result = None

        if 'find' in name_parts and result is not None:
            result = find(result,
                    do_not_fetch=True)
        elif 'obj' in name_parts and result is not None:
            result = AcObject.get_by_url(url=result)

        return result

    def __setitem__(self, name, value):

        value = _normalise_type_for_thing(value)

        logger.debug('  -- %8s %12s %s',
                self.id,
                name,
                value,
                )

        if hasattr(self, 'f_'+name):
            setattr(self, 'f_'+name, value)
            self.save()
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

            if self.pk is None:
                # See above
                self.save()

            try:
                another = ThingField.objects.get(
                        parent = self,
                        field = name,
                        )
            except ThingField.DoesNotExist:
                another = ThingField(
                        parent = self,
                        field = name,
                        )

            another.value = json.dumps(value)
            another.save()

        # Special-cased side effects:

        if name=='tag':

            # We must save, in order for Mention's fk to point to us
            self.save()

            Mention.set_from_tags(
                    status=self,
                    tags=value,
                    )
    @property
    def audiences(self):
        return Audience.get_audiences_for(self)

    def run_side_effects(self):

        from django_kepi.find import find
        from django_kepi.delivery import deliver

        f_type = self.f_type.lower()

        if not hasattr(side_effects, f_type):
            logger.debug('  -- no side effects for %s',
                    f_type)
            return True

        result = getattr(side_effects, f_type)(self)

        return result

    @property
    def is_local(self):
        return self.id.startswith('/')

    def entomb(self):
        logger.info('%s: entombing', self)

        if self['former_type'] is not None:
            logger.warn('   -- already entombed; ignoring')
            return

        if not self.is_local:
            raise ValueError("%s: you can't entomb remote things",
                    self)

        self['former_type'] = self.f_type
        self['deleted'] = timezone.now()

        self.save()
        logger.info('%s: entombed', self)

    def save(self, *args, **kwargs):

        try:
            super().save(*args, **kwargs)
            logger.debug('%s: saved', self)
        except IntegrityError as ie:
            if self.is_local and kwargs.get('_tries_left',0)>0:
                logger.info('Integrity error on save (%s); retrying',
                        ie)
                self.id = _new_number()
                kwargs['_tries_left'] -= 1
                return self.save(*args, **kwargs)
            else:
                logger.info('Integrity error on save (%s); failed',
                        ie)
                raise ie

    @classmethod
    def get_by_url(cls, url):
        """
        Retrieves an AcObject whose URL is "url".

        This differs from find() in that it can
        find objects which were submitted to us over HTTP
        (as opposed to generated locally or fetched by us).
        find() would ignore these.
        """

        from django_kepi.find import find

        logger.debug('     -- finding object with url %s', url)
        result = find(url,
                local_only = True)

        if result is None:
            logger.debug('       -- not local; trying remote')
            try:
                result = cls.objects.get(
                        id = url,
                        )
            except cls.DoesNotExist:
                result = None

        logger.debug('       -- found %s', result)
        return result

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
    elif isinstance(v, AcObject):
        return v.url # AcObjects can deal with themselves

    # okay, it's something weird

    try:
        return v.activity_form
    except AttributeError:
        return str(v)


