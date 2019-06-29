from django.db import models, IntegrityError
from django.conf import settings
from django_kepi.find import find, is_local
from django_kepi.delivery import deliver
from polymorphic.models import PolymorphicModel
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

        for fieldname in ['actor', 'name']:

            value = getattr(self, 'f_'+fieldname)
            if value:
                result[fieldname] = value

        for f in ThingField.objects.filter(parent=self):
            result[f.name] = json.loads(f.value)

        # FIXME test for this was omitted; add it in
        result.update(django_kepi.models.audience.Audience.get_audiences_for(self))

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
        elif name=='number':
            result = self.number
        else:
            try:
                field = ThingField.objects.get(
                        parent = self,
                        name = name,
                        )
                result = field.value

            except ThingField.DoesNotExist:
                result = None

            if 'raw' not in name_parts and result is not None:
                result = json.loads(result)

        if 'obj' in name_parts and result is not None:
            result = find(result,
                    local_only=True)

        return result

    def __setitem__(self, name, value):

        value = _normalise_type_for_thing(value)

        if name=='name':
            self.f_name = value
            self.save()
        elif name=='actor':
            self.f_actor = value
            self.save()
        elif name=='type':
            self.f_type = value
            self.save()
        elif name=='number':
            raise ValueError("Can't set the number of an existing Thing")
        else:

            value = json.dumps(value)

            try:
                field = ThingField.objects.get(
                        parent = self,
                        name = name,
                        )
                field.value = value
                field.save()

            except ThingField.DoesNotExist:
                field = ThingField(
                        parent = self,
                        name = name,
                        value = value
                        )
                field.save()

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

        elif self.f_type=='Create':

            from django_kepi.create import create

            raw_material = self['object']
            creation = create(**raw_material,
                    run_side_effects = False)
            self['object'] = creation
            self.save()

        elif self.f_type in OTHER_OBJECT_TYPES:
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
