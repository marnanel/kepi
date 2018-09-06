from django.db import models
from django_kepi import register_type, TombstoneException
from django_kepi import models as kepi_models

class ThingUser(models.Model):

    actor = models.OneToOneField(
            kepi_models.Actor,
            on_delete = models.CASCADE,
            primary_key = True)

    ftype = 'Person'

    name = models.URLField(max_length=256)

    favourite_colour = models.CharField(
            max_length=256,
            default='chartreuse',
            )

    def __str__(self):
        return '[ThingUser {}]'.format(self.name)

    def save(self):
        if self.actor_id is None:
            self.actor = kepi_models.Actor(
                    url=self.url_identifier(),
                    )
            self.actor.save()

            # IDK why I have to do this explicitly:
            self.actor_id = self.actor.pk

        super().save(self)

    @property
    def activity(self):

        if self.name=='Queen Anne':
            raise TombstoneException(original_type=self.ftype)

        return {
                'id': self.url_identifier(),
                'type': self.ftype,
                'name': self.name,
                'favourite_colour': self.favourite_colour,
                }

    def url_identifier(self):
        return 'https://example.com/user/{}'.format(
                self.name,
                )

    @classmethod
    def find_activity(self, url):
        return None # XXX stub

register_type('Person', ThingUser)

class ThingArticle(models.Model):

    title = models.CharField(max_length=256)
    ftype = 'Article'

    def serialize(self):
        return {
                'id': self.url_identifier(),
                'type': 'Article',
                'title': self.title,
                }
        
    def url_identifier(self):
        return 'https://articles.example.com/{}'.format(
                self.title,
                )

    @classmethod
    def activity_create(cls, type_name, actor, fields):
        pass

    @classmethod
    def activity_update(cls, type_name, actor, fields, partial):
        pass

    @classmethod
    def activity_delete(cls, type_name, actor):
        pass

    @classmethod
    def activity_like(cls, type_name, actor, fobject):
        pass

    @classmethod
    def find_activity(self, url):
        return None # XXX stub


register_type('Article', ThingArticle)

