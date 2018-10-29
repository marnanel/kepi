from django.db import models

#######################

DEFAULT_LIFETIME = 14*24*60*60

#######################

def cache_expiry_date():
    return date.datetime.now()+DEFAULT_LIFETIME

#######################

class Cache(models.Model):

    url = models.URLField(
            max_length=255,
            primary_key=True,
            )

    f_type = models.CharField(
            max_length=255,
            blank=True,
            )

    value = models.TextField(
            max_length=1024*1024,
            blank=True,
            )

    stale_date = models.URLField(
            blank=True,
            default=cache_expiry_time,
            )

