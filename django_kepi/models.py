from django.db import models
from django_kepi import object_type_registry
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import datetime

# Cobject is our name for the ActivityPub class named "Object".
# fobject is our name for the field "object" within an ActivityPub class

class Cobject(models.Model):

    class Meta:
        abstract = True

    verified = models.BooleanField(default=False)
    remote_id = models.URLField(blank=True, null=True, default=None)
    published = models.DateTimeField(default=datetime.datetime.now)
    updated = models.DateTimeField(default=datetime.datetime.now)

    def activity_fields(self):

        result = {
            'id': self.pk,
            'type': self.__class__.__name__,
            'published': self.published, # XXX format
            'updated': self.updated, # XXX format
            }

        for (field, method_name) in [
                ('actor', None),
                ('object', 'fobject'),
                ('published', None),
                ('updated', None),
                ('target', None),
                ]:

            if method_name==None:
                method_name = field

            if hasattr(self.__class__, method_name):
                method = getattr(self.__class__, method_name)

                if callable(method):
                    result[field] = str(method())
                else:
                    result[field] = str(method)

        return result

class Activity_with_actor_and_fobject(Cobject):

    class Meta:
        abstract = True

    actor_type = models.ForeignKey(ContentType,
            on_delete=models.CASCADE,
            related_name='+')
    actor_id = models.PositiveIntegerField()
    actor = GenericForeignKey('actor_type', 'actor_id')
   
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
    pass

class Update(Activity_with_actor_and_fobject):
    # XXX note we're only doing server-to-server here,
    # so the fobject is a complete rewrite.
    # in client-to-server, the fobject is a patch.
    pass

class Delete(Activity_with_actor_and_fobject):
    pass

class Tombstone(Cobject):
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
