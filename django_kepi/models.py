from django.db import models
from django_kepi import object_type_registry, resolve, NeedToFetchException
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import random
import json
import datetime
import warnings

# Cobject is our name for the ActivityPub class named "Object".
# fobject is our name for the field "object" within an ActivityPub class

RESOLVE_FAILSAFE = 10
SERIALIZE = 'serialize'
URL_IDENTIFIER = 'url_identifier'

class VerifiedObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(
                # Local objects are necessarily verified
                remote_id__isnull=False,
                verified=False,
                )

class Cobject(models.Model):

    class Meta:
        abstract = True

    objects = VerifiedObjectsManager()
    all_objects = models.Manager()

    def random_slug():
        result = ''

        for i in range(6):
            digit = random.randint(0, 35)
            
            # yes, I know this can be done more efficiently.
            # I want it to be readable.

            if digit<10:
                result += chr(ord('0')+digit)
            else:
                result += chr(ord('a')+(digit-10))

        return result

    slug = models.SlugField(
            primary_key = True,
            default = random_slug,
            editable = False,
            )

    verified = models.BooleanField(default=False)
    remote_id = models.URLField(blank=True, null=True, default=None)
    published = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)

    def url_identifier(self):
        if self.remote_id is not None:
            return self.remote_id
        else:
            return settings.KEPI['ACTIVITY_URL_FORMAT'] % (self.slug, )

    def is_local(self):
        return self.remote_id is None

    def serialize(self):

        result = {
            'id': self.url_identifier(),
            'type': self.__class__.__name__,
            }

        for (field, field_name) in [
                ('actor', None),
                ('object', 'fobject'),
                ('published', None),
                ('updated', None),
                ('target', None),
                ]:

            if field_name==None:
                field_name = field

            try:
                if getattr(self.__class__, field_name+'_as_url')()==True:
                    method_name = URL_IDENTIFIER
                else:
                    method_name = SERIALIZE
            except AttributeError:
                method_name = SERIALIZE

            if hasattr(self, field_name):
                value = getattr(self, field_name)

                iterations = 0

                while callable(value) or hasattr(value.__class__, method_name):

                    if callable(value):
                        value = value()
                    elif hasattr(value.__class__, method_name):
                        value = getattr(value.__class__, method_name)(value)

                    iterations += 1

                    if iterations >= RESOLVE_FAILSAFE:
                        warnings.warn('serializing {} for {} took too many iterations'.format(
                            self,
                            field_name,
                            ))
                        break

                result[field] = value

        return result

    def serialize_as_str(self):

        def json_default(obj):

            if isinstance(obj, datetime.datetime):
                return obj.isoformat()+'Z'
            else:
                raise TypeError("{} is not serializable".format(
                    type(obj)))

        return json.dumps(
                self.serialize(),
                sort_keys=True,
                indent=2, # no reason not to be pretty
                default=json_default,
                )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.remote_id is None:
            self.deploy()

    def deploy(self):
        pass

class Activity_with_actor_and_fobject(Cobject):

    class Meta:
        abstract = True

    actor_type = models.ForeignKey(ContentType,
            on_delete=models.CASCADE,
            related_name='+')
    actor_id = models.PositiveIntegerField()
    actor = GenericForeignKey('actor_type', 'actor_id')
    actor_as_url = lambda: True
   
    fobject_type = models.ForeignKey(ContentType,
            on_delete=models.CASCADE,
            related_name='+')
    fobject_id = models.PositiveIntegerField()
    fobject = GenericForeignKey('fobject_type', 'fobject_id')

class Activity_with_target_and_fobject(Cobject):

    class Meta:
        abstract = True

    target_type = models.ForeignKey(ContentType,
            on_delete=models.CASCADE,
            related_name='+')
    target_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_type', 'target_id')
   
    fobject_type = models.ForeignKey(ContentType,
            on_delete=models.CASCADE,
            related_name='+')
    fobject_id = models.PositiveIntegerField()
    fobject = GenericForeignKey('fobject_type', 'fobject_id')

class Activity_with_fobject(Cobject):

    class Meta:
        abstract = True

    fobject_type = models.ForeignKey(ContentType,
            on_delete=models.CASCADE,
            related_name='+')
    fobject_id = models.PositiveIntegerField()
    fobject = GenericForeignKey('fobject_type', 'fobject_id')

class Create(Activity_with_actor_and_fobject):

    def deploy(self):
        object_type_registry[self.fobject.ftype].activity_create(
                type_name = self.fobject.ftype,
                fields = self.fobject,
                actor = self.actor,
                )

class Update(Activity_with_actor_and_fobject):
    # True in client-to-server, where the fobject is a patch.
    partial = models.BooleanField(default=False)

    def deploy(self):
        object_type_registry[self.fobject.ftype].activity_update(
                type_name = self.fobject.ftype,
                fields = self.fobject,
                actor = self.actor,
                partial = self.partial,
                )

class Delete(Activity_with_actor_and_fobject):

    def deploy(self):

        if object_type_registry[self.fobject.ftype].activity_delete(
                type_name = self.fobject.ftype,
                actor = self.actor,
                ):

            pass # XXX create Tombstone

class Tombstone(models.Model):

    class Meta:
        indexes = [
                models.Index(fields=['ftype', 'slug']),
                ]

    ftype = models.CharField(max_length=20)
    slug = models.SlugField()

    published = models.DateTimeField()
    updated = models.DateTimeField(default=datetime.datetime.now)
    deleted = models.DateTimeField(default=datetime.datetime.now)

class Follow(Activity_with_actor_and_fobject):
    pass

class Add(Activity_with_target_and_fobject):
    pass

class Remove(Activity_with_target_and_fobject):
    pass

class Like(Activity_with_actor_and_fobject):
    pass

class Undo(Activity_with_fobject):
    pass

class Accept(Activity_with_fobject):
    pass

class Reject(Activity_with_fobject):
    pass

def deserialize(s):

    try:
        del s['id']
    except AttributeError:
        pass

    if 'type' not in s:
        raise ValueError("can't deserialize without a type")

    raise ValueError("nyi")

# TODO there are better ways to do this
ACTIVITY_TYPES = {
        "create": Create,
        "update": Update,
        "delete": Delete,
        # Tombstone can't be accessed directly
        "follow": Follow,
        "add": Add,
        "remove": Remove,
        "like": Like,
        "undo": Undo,
        "accept": Accept,
        "reject": Reject,
        }

def lookup(ftype, slug):

    if ftype not in ACTIVITY_TYPES:
        raise TypeError("{} is not an Activity type".format(
            ftype,
            ))

    result = ACTIVITY_TYPES[ftype].objects.get(slug=slug)

    if result is None:
        result = Tombstone.objects.get(ftype=ftype, slug=slug)

    return result

def create(ftype,
        remote_id=None):

    if ftype not in ACTIVITY_TYPES:
        raise TypeError("{} is not an Activity type".format(
            ftype,
            ))

    result = ACTIVITY_TYPES[ftype](remote_id=remote_id)

    return result

###############################

class Actor(models.Model):
    url = models.URLField(max_length=256)

    def __str__(self):
        return '[Actor {}]'.format(self.url)

###############################

class UserRelationship(models.Model):

    class Meta:
        abstract = True

class Following(UserRelationship):

    follower = models.ForeignKey(Actor,
            on_delete = models.CASCADE,
            related_name = 'followers')
    following = models.ForeignKey(Actor,
            on_delete = models.CASCADE,
            related_name = 'following')

    def __str__(self):
        return '({} follows {})'.format(
                self.follower.name,
                self.following.name,
                )

class Blocking(UserRelationship):

    blocker = models.ForeignKey(Actor,
            on_delete = models.CASCADE,
            related_name = 'blockers')
    blocking = models.ForeignKey(Actor,
            on_delete = models.CASCADE,
            related_name = 'blocking')

    def __str__(self):
        return '({} blocks {})'.format(
                self.follower.name,
                self.following.name,
                )

class RequestingAccess(UserRelationship):

    hopeful = models.ForeignKey(Actor,
            on_delete = models.CASCADE,
            related_name = 'hopefuls')
    grantor = models.ForeignKey(Actor,
            on_delete = models.CASCADE,
            related_name = 'grantors')

    def __str__(self):
        return '({} requests {})'.format(
                self.follower.name,
                self.following.name,
                )

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

    def deploy(self):
        pass

#######################

def new_activity_identifier():
    template = settings.KEPI['ACTIVITY_URL_FORMAT']
    slug = '%08x' % (random.randint(0, 0xffffffff),)
    return template % (slug,)

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

    atype = models.URLField(
            max_length=1,
            choices=ACTIVITY_TYPE_CHOICES,
            )

    identifier = models.URLField(
            max_length=255,
            primary_key=True,
            default=new_activity_identifier,
            )

    actor = models.URLField(
            max_length=255,
            blank=True,
            )

    fobject_type = models.CharField(
            max_length=255,
            blank=True,
            )

    fobject = models.URLField(
            max_length=255,
            blank=True,
            )

    target = models.URLField(
            max_length=255,
            blank=True,
            )

    active = models.BooleanField(
            default=True,
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
                self.atype,
                self.identifier,
                inactive_warning,
                )
        return result

    @property
    def activity(self):
        result = {
            'id': self.identifier,
            'atype': self.get_atype_display(),
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
            'Accept': (False, True,   False),
            'Reject': (False, True,   False),
            }

    @classmethod
    def deserialize(cls, value,
            local=False):

        if 'type' not in value:
            raise ValueError("Activities must have a type")

        if 'id' not in value and not local:
            raise ValueError("Remote activities must have an id")

        fields = {
                'identifier': value.get('id', None),
                'atype': value['type'],
                'active': True,
                }

        try:
            need_actor, need_object, need_target = cls.TYPES[value['type']]
        except KeyError:
            raise ValueError('{} is not an Activity type'.format(value['type']))

        if need_actor!=('actor' in value) or \
                need_object!=('object' in value) or \
                need_target!=('target' in value):

                    raise ValueError('Wrong parameters for type')

        # TODO: Sometimes an incoming Activity is trustworthy in
        # telling us about a remote object. At present, for
        # simplicity, we don't trust anybody. If we don't have
        # the object in the cache, we must fetch it.

        # In each case, the field is either specified as
        # a Link or as an Object. If it's a Link, it will
        # consist of a single string, which is our URL.
        # If it's an Object, it will be a dict whose 'id'
        # field is our URL.

        for ftype in ('actor', 'object', 'target'):

            if ftype not in value:
                # if it's not there, it's not supposed to be there:
                # we checked for that earlier.
                continue

            if isinstance(value[ftype], str):
                check_url = value[ftype]
                check_type = None # check everything
            else:
                try:
                    check_url = value[ftype]['id']
                except KeyError:
                    raise ValueError('Explicit objects must have an id')

                try:
                    check_type = value[ftype]['type']
                except KeyError:
                    check_type = None # check everything

                referent = resolve(
                        identifier=check_url,
                        atype=check_type,
                        )

                if referent is None:
                    # we don't know about it,
                    # but we need to.
                    raise NeedToFetchException(check_url)

                # okay, we can let them use it

                if ftype=='object':
                    fieldname='fobject'
                else:
                    fieldname=ftype

                fields[fieldname] = check_url

        result = cls(**fields)
        result.save()

        return result

    # TODO: there should be a clean() method with the same
    # checks as deserialize().

