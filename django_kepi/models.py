from django.db import models
from django_kepi import object_type_registry
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from random import randint
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
            digit = randint(0, 35)
            
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
            return settings.KEPI['URL_FORMAT'] % {
                    'type': self.__class__.__name__.lower(),
                    'slug': self.slug,
                    }

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

class UnexpiredNamedObjectsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(
                #expiry==datetime.datetime.now(),
                )

class NamedObject(models.Model):
    """
    This table maps URL identifiers to Django objects, using the
    contenttypes mechanism. It also keeps track of the object's
    ActivityObject type.

    Any object we know about on a remote server must be listed
    here. Objects on this server *may* be listed here; if they're not,
    django_kepi.resolve() can also find them
    through following the URL path.
    """

    url = models.URLField(
            max_length=255,
            primary_key=True,
            )

    activity_type = models.CharField(
            max_length=255,
            )

    expiry = models.DateTimeField(default=None)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    objects = UnexpiredNamedObjectsManager()
    all_objects = models.Manager()

def resolve(identifier):

    try:
        result = NamedObject.objects.get(url=identifier)
        return result
    except NamedObject.DoesNotExist:
        pass

    return None
