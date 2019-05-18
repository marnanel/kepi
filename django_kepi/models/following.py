from django.db import models
from django_kepi.models.thing import Thing

logger = logging.getLogger(name='django_kepi')

class Following(models.Model):

    follower = models.URLField(
            max_length=255,
            )

    following = models.URLField(
            max_length=255,
            )

    pending = models.BooleanField(
            default=True,
            )

    def __str__(self):

        if self.pending:
            pending = ''
        else:
            pending = ' (pending acceptance)'

        result = '[%s follows %s%s]' % (
                self.follower,
                self.following,
                pending,
                )
        return result


