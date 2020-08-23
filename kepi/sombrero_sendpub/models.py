# fetch.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.db import models
from kepi.bowler_pub.utils import configured_url, as_json
from django.db.models.constraints import UniqueConstraint
import django.utils.timezone
import json

class OutgoingActivity(models.Model):

    content = models.TextField()

    @property
    def url(self):
        return configured_url(
                'ACTIVITY_LINK',
                serial = self.pk,
                )

    @property
    def value(self):
        result = json.loads(self.content)

        if 'id' not in result:
            result['id'] = self.url

        if '@context' not in result:
            from kepi.bowler_pub import ATSIGN_CONTEXT
            result['@context'] = ATSIGN_CONTEXT

        return result

    def __repr__(self):
        return as_json(self.value)

    def __str__(self):
        return self.__repr__()

    def save(self, *args, **kwargs):

        if not isinstance(self.content, str):

            for field in ['type',]:
                if field not in self.content:
                    raise ValueError("activity is missing required fields: "+\
                            str(self.content))

            self.content = json.dumps(self.content)

        super().save(*args, **kwargs)

class WebfingerUser(models.Model):

    username = models.CharField(
            max_length = 256,
            )

    hostname = models.CharField(
            max_length = 256,
            )

    url = models.URLField(
            blank = True,
            null = True,
            default = None,
            )

    fetched = models.DateTimeField(
            default=django.utils.timezone.now,
            )

    class Meta:
        constraints = [
                UniqueConstraint(
                    fields = ['username', 'hostname'],
                    name = 'user_and_host',
                    ),
                ]

    def __str__(self):
        return f'{self.username}@{self.hostname} -> {self.url}'
