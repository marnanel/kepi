# mention.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.db import models
from django.db.models.constraints import UniqueConstraint

class Mention(models.Model):

    status = models.ForeignKey(
            'Status',
            on_delete = models.DO_NOTHING,
            )

    whom = models.ForeignKey(
            'Person',
            on_delete = models.DO_NOTHING,
            )

    class Meta:
        constraints = [
                UniqueConstraint(
                    fields = ['status', 'whom'],
                    name = 'mention_unique',
                    ),
                ]

    def __str__(self):
        return '[%s mentions %s]' % (self.status, self.whom)
