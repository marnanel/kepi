from django.db import models
from django_kepi import register_type

class ThingUser(models.Model):

    name = models.CharField(max_length=256)
    #activity_object = models.OneToOneField(
    #        ActivityObject,
    #        on_delete=models.CASCADE,
    #        )

    def serialize(self):
        return {
                'id': self.url_identifier(),
                'type': 'Person',
                'name': self.name,
                }

    def url_identifier(self):
        return 'https://example.com/user/{}'.format(
                self.name,
                )

class ThingArticle(models.Model):

    title = models.CharField(max_length=256)

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


