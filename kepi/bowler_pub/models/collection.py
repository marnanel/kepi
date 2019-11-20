from django.db import models
from django.conf import settings
from .acobject import AcObject
import logging

logger = logging.getLogger(name='kepi')

class Collection(models.Model):

    owner = models.ForeignKey(
            'bowler_pub.AcActor',
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

    @classmethod
    def get(cls,
            user,
            collection,
            create_if_missing=True):
        """
        Returns a particular Collection.

        If the named collection does not exist,
        and if create_if_missing is True (the default),
        then an empty collection of that name will be created and returned.

        Otherwise, we raise KeyError.
        """

        logger.debug('Finding collection "%s" for %s',
                collection, user.id)

        try:
            result = cls.objects.get(
                    owner = user,
                    name = collection,
                    )
            logger.debug('  -- found %s', result)

            return result

        except cls.DoesNotExist:

            if create_if_missing:

                newCollection = cls(
                        owner = user,
                        name = collection,
                        )
                newCollection.save()
                logger.debug('  -- not found; created %s',
                        newCollection)

                return newCollection

            else:
                logger.debug(' -- not found')
                raise KeyError(collection)

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

    @property
    def members(self):
        result = AcObject.objects.filter(
                collectionmember__parent = self,
                )

        return result

class CollectionMember(models.Model):

    parent = models.ForeignKey(
        Collection,
        on_delete = models.CASCADE,
        )

    member = models.ForeignKey(
            'bowler_pub.AcObject',
            on_delete = models.DO_NOTHING,
            )

    def __str__(self):

        return '  -- %s %s' % (
                self.parent,
                self.member,
                )


