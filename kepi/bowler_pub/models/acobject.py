from django.db import models, IntegrityError
from django.conf import settings
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from polymorphic.managers import PolymorphicManager
from kepi.bowler_pub.models.audience import Audience, AUDIENCE_FIELD_NAMES
from kepi.bowler_pub.models.thingfield import ThingField
from kepi.bowler_pub.models.mention import Mention
from kepi.bowler_pub.utils import configured_path, uri_to_url
from .. import URL_REGEXP, LOCAL_NUMBER_REGEXP
import kepi.bowler_pub.side_effects as side_effects
import logging
import random
import warnings
import re

logger = logging.getLogger(name='kepi')

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

        LOCAL_ONLY = 'id__regex'

        if LOCAL_ONLY in kwargs:
            raise ValueError(('%s is already an argument; '+\
                    'this should never happen') % (LOCAL_ONLY,))
        kwargs[LOCAL_ONLY] = r'^[/@]'

######################

class AcObject(PolymorphicModel):

    id = models.CharField(
            max_length=255,
            primary_key=True,
            unique=True,
            blank=False,
            default=None,
            editable=False,
            )

    objects = KepiManager()

    published = models.DateTimeField(
            default = timezone.now,
            )

    updated = models.DateTimeField(
            auto_now = True,
            )

    serial = models.IntegerField(
            default = 0,
            )

    @property
    def url(self):
        uri = self.uri

        if uri is None:
            return self.id
        else:
            return uri_to_url(uri)

    @property
    def uri(self):
        if self.id.startswith('/'):
            return configured_path('OBJECT_LINK',
                    number = self.id[1:],
                    )
        elif self.id.startswith('@'):
            return configured_path('USER_LINK',
                    username = self.id[1:],
                    )
        else:
            return None

    @property
    def number(self):
        if self.is_local:
            return self.id[1:]
        else:
            return None

    def __str__(self):

        result = '[%s %s]' % (
                self.id,
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

    def items(self):
        return self.activity_form.items()

    @property
    def activity_form(self):

        from kepi.bowler_pub.utils import short_id_to_url

        result = {
            'id': self.url,
            'type': self.f_type,
            'published': self.published,
            }

        for name in dir(self):
            if not name.startswith('f_'):
                continue

            value = getattr(self, name)
            value = short_id_to_url(value)

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

        from kepi.bowler_pub.find import find

        name_parts = name.split('__')
        name = name_parts.pop(0)

        if hasattr(self, 'f_'+name):
            result = getattr(self, 'f_'+name)
        elif name in [
                'published',
                'updated',
                'url',
                'id',
                ]:
            result = getattr(self, name)
        elif name in AUDIENCE_FIELD_NAMES:
            try:
                result = Audience.get_audiences_for(
                        thing = self,
                        audience_type = name,
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
        elif name in [
                'published',
                ]:
            setattr(self, name, value)
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

            from kepi.bowler_pub.utils import as_json

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


            another.value = as_json(value)
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

    def run_side_effects(self, **kwargs):

        from kepi.bowler_pub.find import find
        from kepi.bowler_pub.delivery import deliver

        f_type = self.f_type.lower()

        if not hasattr(side_effects, f_type):
            logger.debug('  -- no side effects for %s',
                    f_type)
            return True

        result = getattr(side_effects, f_type)(
                self,
                **kwargs,
                )

        return result

    @property
    def is_local(self):
        return self.id and self.id[0] in '@/'

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

    def _generate_id(self):
        """
        Returns a value for "id" on a new object, where
        the caller has omitted to supply an "id" value.
        The new value should be unique.

        If this method returns None, the object will
        not be created.
        """
        return '/%08x' % (random.randint(0, 0xffffffff),)

    def _check_provided_id(self):
        """
        Checks self.id to see whether it's valid for
        this kind of AcObject. It may normalise the value.

        If the value is valid, returns.
        If the value is invalid, raises ValueError.

        This method is not called if self.id is a valid
        URL, because that means it's a remote object
        and our naming rules won't apply.
        """
        if re.match(LOCAL_NUMBER_REGEXP, self.id,
                re.IGNORECASE):

            self.id = self.id.lower()
            logger.debug('id==%s which is a valid local number',
                    self.id)
            return

        raise ValueError("Object IDs begin with a slash "+\
                "followed by eight characters from "+\
                "0-9 or a-f. "+\
                "You gave: "+self.id)

    def save(self, *args, **kwargs):

        if self.serial==0:
            max_so_far = AcObject.objects.filter(
                    ).aggregate(models.Max('serial'))['serial__max']

            if max_so_far is None:
                max_so_far = 0

            self.serial = max_so_far + random.randint(0, 256)

            logger.info('  -- max serial so far is %d; using serial %d',
                    max_so_far, self.serial)

        if self.id is None:
            self.id = self._generate_id()

            if self.id is None:
                raise ValueError("You need to specify an id "+\
                        "on %s objects." % (self.__class__.__name__,))
        else:
            if re.match(URL_REGEXP, self.id,
                    re.IGNORECASE):
                logger.debug('id==%s which is a valid URL',
                        self.id)
            else:
                self._check_provided_id()

        try:
            super().save(*args, **kwargs)
            logger.debug('%s: saved', self)
        except IntegrityError as ie:
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

        from kepi.bowler_pub.find import find

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
        return v.short_id # AcObjects can deal with themselves

    # okay, it's something weird

    try:
        return v.activity_form
    except AttributeError:
        return str(v)


