from django.db import models
from django_kepi import implements_activity_type, TombstoneException
from django_kepi import models as kepi_models
import logging

logger = logging.getLogger(name='things_for_testing')

@implements_activity_type('Person')
class ThingUser(models.Model):

    name = models.CharField(max_length=256)
    public_key = models.CharField(max_length=256)
    private_key = models.CharField(max_length=256)

    favourite_colour = models.CharField(
            max_length=256,
            default='chartreuse',
            )

    def __str__(self):
        return '[ThingUser {}]'.format(self.name)

    @property
    def url(self):
        return 'https://altair.example.com/users/{}'.format(
                self.name,
                )

    @property
    def key_name(self):
        return self.url+'#main-key'

    @property
    def activity_form(self):

        if self.name=='Queen Anne':
            raise TombstoneException(original_type=self.implements_activity_type)

        return {
                'id': self.url,
                'type': self.implements_activity_type,
                'name': self.name,
                'favourite_colour': self.favourite_colour,
                }

    @property
    def activity_id(self):
        return self.url

    @property
    def activity_followers(self):
        return self.url+'/followers'

    @property
    def activity_following(self):
        return self.url+'/following'

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
            url=fields['id'],
            name=fields['id'],
            )
        result.save()
        return result

@implements_activity_type('Note')
class ThingNote(kepi_models.ActivityModel):

    title = models.CharField(max_length=256)
    f_type = 'Note'

    remote_url = models.URLField(max_length=256,
            null=True, default=None)

    owner = models.URLField(max_length=256)

    @property
    def activity_actor(self):
        return self.owner

    @property
    def activity_form(self):
        return {
                'id': self.activity_id,
                'type': 'Note',
                'title': self.title,
                }
        
    @property
    def activity_id(self):
        return 'https://articles.example.com/{}'.format(
                self.title.replace(' ','-').lower(),
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
