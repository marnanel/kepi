from django.db import models
from django.conf import settings
import logging

logger = logging.getLogger(name='django_kepi')

class Collection(models.Model):

    owner = models.ForeignKey(
            'django_kepi.AcActor',
            on_delete = models.DO_NOTHING,
            )

    name = models.URLField(
            max_length=255,
            )

    class Meta:
        constraints = [
                models.UniqueConstraint(
                    fields = ['owner', 'name'],
                    name = 'owner and name',
                    ),
                ]

    @property
    def path(self):
        return self.owner.list_path(self.name)

    def append(self, what):

        logger.info('Collection %s gains %s',
                self, what)

        newMember = CollectionMember(
                parent = self,
                member = what,
                )
        newMember.save()

    def __str__(self):
        return '%s/%s' % (
                self.owner.id,
                self.name,
                )

    # FIXME it ought to be possible to specify username and collectionname
    # instead of just name here

    @classmethod
    def get(cls, name,
            create_if_missing=True):

        from django_kepi.models.actor import AcActor

        try:
            username, collectionname = name.split('/')
        except ValueError:
            logger.info('collection id in wrong format: %s',
                    name)
            raise ValueError('Format of name is "username/collectionname": %s',
                    name)

        logger.debug('Finding collection %s/%s',
                username, collectionname)

        try:
            owner = AcActor.objects.get(
                    id = '@'+username,
                    )
        except AcActor.DoesNotExist:
            logger.info("  -- can't get %s because %s doesn't exist",
                    name, username,
                    )
            raise KeyError(name)

        try:
            result = cls.objects.get(
                    owner = owner,
                    name = collectionname,
                    )
            logger.debug('  -- found %s', result)

            return result

        except cls.DoesNotExist:

            if create_if_missing:

                newCollection = cls(
                        owner = owner,
                        name = collectionname,
                        )
                newCollection.save()
                logger.debug('  -- not found; created %s',
                        newCollection)

                return newCollection

            else:
                logger.debug(' -- not found')
                raise KeyError(name)

    @classmethod
    def build_name(cls,
            username, collectionname):

        if username is None:
            raise ValueError('Username not supplied')

        if collectionname is None:
            raise ValueError('Collectionname not supplied')

        if '/' in username:
            raise ValueError('Username cannot contain slashes')

        if '/' in collectionname:
            raise ValueError('Collectionname cannot contain slashes')

        if not username:
            raise ValueError('Username cannot be blank')

        if not collectionname:
            raise ValueError('Collectionname cannot be blank')

        return '%s/%s' % (username, collectionname)

class CollectionMember(models.Model):

    parent = models.ForeignKey(
        Collection,
        on_delete = models.CASCADE,
        )

    member = models.ForeignKey(
            'django_kepi.AcObject',
            on_delete = models.DO_NOTHING,
            )

    def __str__(self):

        return '  -- %s %s' % (
                self.parent,
                self.member,
                )


