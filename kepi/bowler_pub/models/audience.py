from django.db import models
from collections import defaultdict
from .. import PUBLIC_IDS
import logging

logger = logging.getLogger('kepi')

FIELD_AUDIENCE = 0x01 # literally "audience"
FIELD_TO       = 0x02 
FIELD_CC       = 0x04

BLIND          = 0x70
FIELD_BTO = BLIND + FIELD_TO
FIELD_BCC = BLIND + FIELD_CC
# the spec doesn't allow for blind audience; idk why

FIELD_CHOICES = [
        (FIELD_AUDIENCE, 'audience'),
        (FIELD_TO,       'to'),
        (FIELD_CC,       'cc'),
        (FIELD_BTO,      'bto'),
        (FIELD_BCC,      'bcc'),
        ]

AUDIENCE_FIELD_NAMES = dict([(v,f) for (f,v) in FIELD_CHOICES])
AUDIENCE_FIELD_KEYS = set([v for (f,v) in FIELD_CHOICES])

class Audience(models.Model):

    parent = models.ForeignKey(
            'bowler_pub.AcObject',
            on_delete = models.CASCADE,
            )

    field = models.PositiveSmallIntegerField(
            choices = FIELD_CHOICES,
            )

    recipient = models.CharField(
            max_length=255,
            )

    @property
    def blind(self):
        return (self.field & BLIND) != 0

    def __str__(self):
        return '[%s %12s %s]' % (
                self.parent.id,
                self.get_field_display(),
                self.recipient,
                )

    @classmethod
    def add_audiences_for(cls, thing,
            field, value):

        """
        Add new Audiences for a given Object.
        "value" is a list of strings.

        This function only adds Audiences of
        a single field type. This is
        deliberately asymmetrical to
        get_audiences_for(), which returns
        all Audiences of all field types.
        The difference is because of
        where it's needed.
        """
        
        if field not in AUDIENCE_FIELD_NAMES:
            raise ValueError('%s is not an audience field' % (
                field,
                ))

        field = AUDIENCE_FIELD_NAMES[field]

        if value is None:
            value = []
        elif not isinstance(value, list):
            value = [str(value)]
        else:
            value = [str(x) for x in value]

        for line in value:
            a = cls(
                parent = thing,
                field = field,
                recipient = line,
                )
            a.save()

    @classmethod
    def get_audiences_for(cls, thing,
            audience_type = None,
            hide_blind = False,
            ):

        result = defaultdict(lambda: [])

        for a in cls.objects.filter(
                parent=thing,
                ):

            fieldname = a.get_field_display()

            if audience_type is not None:
                if fieldname!=audience_type:
                    continue

            if hide_blind and a.blind:
                logger.debug('Not counting %s because blind fields are hidden',
                        a)
                continue

            result[fieldname].append(a.recipient)

        if audience_type is not None:
            result = result[audience_type]
        else:
            result = dict(result)

        return result
