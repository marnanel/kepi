from django.db import models
import logging
import json

logger = logging.getLogger(name='kepi')

class ThingField(models.Model):

    class Meta:
        constraints = [
                models.UniqueConstraint(
                    fields = ['parent', 'field'],
                    name = 'parent_field',
                    ),
                ]

    field = models.CharField(
            max_length=255,
            )

    value = models.CharField(
            max_length=255,
            default=None,
            null=True,
            blank=True,
            )

    parent = models.ForeignKey(
            'bowler_pub.AcObject',
            on_delete = models.CASCADE,
            )

    def __str__(self):
        return '%16s: %s' % (
                self.field,
                self.value,
                )

    @property
    def interpreted_value(self):
        if self.value is None:
            return None
        else:
            try:
                return json.loads(self.value)
            except json.decoder.JSONDecodeError:
                logger.warn('Non-JSON value; returning None: %s=%s',
                        self.field, self.value)
                return None

    @classmethod
    def get_fields_for(cls, thing,
            ):

        result = {}

        for a in cls.objects.filter(
                parent=thing,
                ):

            result[a.field] = a.interpreted_value

        return result
