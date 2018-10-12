from django.db import models
from django_kepi import activity_type, TombstoneException
from django_kepi import models as kepi_models
from django_kepi import logger

@activity_type('Person')
class ThingUser(models.Model):

    name = models.CharField(max_length=256)

    favourite_colour = models.CharField(
            max_length=256,
            default='chartreuse',
            )

    remote = models.BooleanField(
            default=False,
            )

    def __str__(self):
        return '[ThingUser {}]'.format(self.name)

    @property
    def activity_form(self):

        if self.name=='Queen Anne':
            raise TombstoneException(original_type=self.activity_type)

        return {
                'id': self.activity_id,
                'type': self.activity_type,
                'name': self.name,
                'favourite_colour': self.favourite_colour,
                }

    @property
    def activity_type(self):
        return 'Person'

    @property
    def activity_id(self):
        if self.remote:
            return self.name
        else:
            return 'https://example.com/user/{}'.format(
                    self.name,
                    )

    @classmethod
    def activity_find(cls, url):
        PREFIX = "https://example.com/user/"

        if url.startswith(PREFIX):
            name = url[len(PREFIX):]
        else:
            name = url

        return cls.objects.get(name=name)

    @classmethod
    def activity_create(cls, fields):
        result = cls(
            name=fields['id'],
            remote=True,
            )
        result.save()
        return result

@activity_type('Article')
class ThingArticle(models.Model):

    title = models.CharField(max_length=256)
    ftype = 'Article'

    remote_url = models.URLField(max_length=256,
            null=True, default=None)

    @property
    def activity_form(self):
        return {
                'id': self.activity_id,
                'type': 'Article',
                'title': self.title,
                }
        
    @property
    def activity_id(self):
        return 'https://articles.example.com/{}'.format(
                self.title,
                )

    @classmethod
    def activity_find(cls, url):
        PREFIX = "https://articles.example.com/"
        if url.startswith(PREFIX):
            title = url[len(PREFIX):]
            return cls.objects.get(title=title)
        else:
            return cls.objects.get(remote_url=url)

    @classmethod
    def activity_create(cls, fields):
        result = cls(
            remote_url=fields['id'],
            title=fields['title'],
            )
        result.save()
        return result

