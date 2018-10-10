from django.db import models
from django_kepi import object_type_registry, resolve, register_type, NeedToFetchException
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

logger = logging.getLogger(__name__)

#######################

class QuarantinedMessage(models.Model):

    username = models.CharField(
            max_length=255,
            blank=True,
            null=True,
            default=None)

    headers = models.TextField()
    body = models.TextField()

    signature_verified = models.BooleanField(
            default=False,
            )

    def deploy(self,
            retrying=False):

        if retrying:
            logger.debug('%s: re-attempting to deploy', self)

            remaining_qmns = QuarantinedMessageNeeds.objects.filter(
                    message=self.pk,
                    )
            
            if remaining_qmns.exists():
                logger.debug('%s:  -- but there are dependencies remaining: %s',
                        self, remaining_qmns)
                return None
        else:
            logger.debug('%s: attempting to deploy', self)

        try:
            value = json.loads(self.body)
        except json.decoder.JSONDecodeError:
            logger.info('%s: JSON was invalid; deleting', self)
            self.delete()
            return None

        try:
            activity = Activity.create(
                    value = value,
                    local = False,
                    )
        except NeedToFetchException as ntfe:
            logger.debug('%s: deployment failed because we need to fetch: %s',
                    self, ntfe.urls)

            if retrying:
                logger.error("%s: dependencies remaining when all dependency records were gone; this should never happen")
                raise RuntimeError("dependencies remaining on retry")

            for need in ntfe.urls:
                qmn = QuarantinedMessageNeeds(
                        message=self,
                        needs_to_fetch=need,
                        )
                qmn.save()
                qmn.start_looking()
                
            return None
        else:
            logger.info('%s: deployment was successful', self)
            self.delete()

        return activity

    def __str__(self):
        return 'QM{}'.format(self.pk)

class QuarantinedMessageNeeds(models.Model):

    class Meta:
        index_together = ["message", "needs_to_fetch"]

    id = models.UUIDField(
            primary_key=True,
            default=uuid.uuid4,
            editable=False,
            )

    message = models.ForeignKey(QuarantinedMessage,
            on_delete=models.CASCADE)

    # TODO: add indexing when we have tests working

    needs_to_fetch = models.URLField()

    def start_looking(self):
        django_kepi.tasks.fetch.delay(
                fetch_url = self.needs_to_fetch,
                post_data = None,
                result_url = 'https://localhost/async_result', # XXX
                result_id = self.id,
                )

    def __str__(self):
        return 'QM{} needs {}'.format(
                self.message.pk,
                self.needs_to_fetch,
                )

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

    accepted = models.BooleanField(
            default=False,
            )

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
    def activity(self):
        result = {
            'id': self.identifier,
            'f_type': self.get_f_type_display(),
            }

        for optional in ['actor', 'object', 'published', 'updated', 'target']:
            if optional=='object':
                fieldname='fobject'
            else:
                fieldname=optional

            value = getattr(self, fieldname)
            if value is not None:
                result[optional] = value

        # XXX should we mark "inactive" somehow?

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

    def deploy(self):
        """
        Some kinds of Activity have side-effects
        when they're created. This method carries out
        those side-effects.
        """
        if self.f_type=='Accept':

            referent = resolve(
                identifier=self.f_object,
                f_type='Follow',
                )

            if referent is not None:
                referent.accepted = True
                referent.save()

        elif self.f_type=='Reject':

            referent = resolve(
                identifier=self.f_object,
                f_type='Follow',
                )

            if referent is not None:
                referent.accepted = False
                referent.active = False
                referent.save()


    @classmethod
    def register_all_activity_types(cls):
        for t in cls.TYPES.keys():
            register_type(t, cls)

    @classmethod
    def find_activity(cls, url):
        return cls.objects.get(identifier=url)

    @classmethod
    def activitypub_create(cls, fields):
        return cls.create(value, local=False)

    @classmethod
    def create(cls, value,
            local=False):

        logger.debug('Creating Activity from %s', str(value))

        if 'type' not in value:
            raise ValueError("Activities must have a type")

        if 'id' not in value and not local:
            raise ValueError("Remote activities must have an id")

        fields = {
                'identifier': value.get('id', None),
                'f_type': value['type'],
                'active': True,
                }

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

        # TODO: Sometimes an incoming Activity is trustworthy in
        # telling us about a remote object. At present, for
        # simplicity, we don't trust anybody. If we don't have
        # the object in the cache, we must fetch it.

        # In each case, the field is either specified as
        # a Link or as an Object. If it's a Link, it will
        # consist of a single string, which is our URL.
        # If it's an Object, it will be a dict whose 'id'
        # field is our URL.

        unresolved_references = set()

        for fieldname in ('actor', 'object', 'target'):

            if fieldname not in value:
                # if it's not there, it's not supposed to be there:
                # we checked for that earlier.
                continue

            obj_id, obj_type = _object_to_id_and_type(value[fieldname])

            referent = resolve(
                identifier=obj_id,
                f_type=obj_type,
                )

            if referent is None:

                # oh, weird. Maybe they got the type wrong.
                referent = resolve(
                    identifier=obj_id,
                    f_type=None,
                    )

                if referent is None:
                    unresolved_references.add(obj_id)

            # okay, we can let them use it

            fields['f_'+fieldname] = obj_id

        if unresolved_references:
            logger.debug('Unresolved references: %s', str(unresolved_references))
            raise NeedToFetchException(unresolved_references)

        result = cls(**fields)
        result.save()
        result.deploy()

        return result

    # TODO: there should be a clean() method with the same
    # checks as create().

########################################

Activity.register_all_activity_types()

