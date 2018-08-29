from django.db import models
from django_kepi import register_type
from django_kepi import models as kepi_models

class ThingUser(kepi_models.YourPerson):

    favourite_colour = models.CharField(
            max_length=256,
            default='chartreuse',
            )

    def serialize(self):

        result = super().serialize()
        result['favourite_colour'] = self.favourite_colour

        return result

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

register_type('Article', ThingArticle)

