from django.db import models
import datetime
import json

#######################

DEFAULT_LIFETIME = 14*24*60*60

#######################

def cache_expiry_time():
    return datetime.datetime.now()+datetime.timedelta(seconds=DEFAULT_LIFETIME)

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

    @property
    def fields(self):
        return json.loads(self.value)

    @fields.setter
    def fields(self, value):
        self.value = json.dumps(value)

    def __getattr__(self, fieldname):

        if fieldname not in self.fields:
            raise ValueError('Field {} doesn\'t exist. Only: {}'.format(
                fieldname,
                ' '.join(sorted(self.fields.keys())),
                ))

        return self.fields[fieldname]
