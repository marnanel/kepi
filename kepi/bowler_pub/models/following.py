from django.db import models
from kepi.bowler_pub.utils import short_id_to_url
import logging

logger = logging.getLogger(name='kepi')

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
            pending = ' (pending acceptance)'
        else:
            pending = ''

        result = '[%s follows %s%s]' % (
                self.follower,
                self.following,
                pending,
                )
        return result

    @classmethod
    def _get_follow(cls, follower, following):
        try:
            return Following.objects.get(follower=follower, following=following)
        except Following.DoesNotExist:
            return None

    @classmethod
    def make_request(cls, follower, following):

        follower = short_id_to_url(follower)
        following = short_id_to_url(following)

        f = cls._get_follow(follower, following)

        if f is not None:
            if f.pending:
                logger.warn('%s has already requested to follow %s',
                        follower, following)
            else:
                logger.warn('%s is already following %s',
                        follower, following)
            return

        result = Following(
                follower = follower,
                following = following,
                pending = True,
                )
        result.save()

        logger.info('%s has requested to follow %s',
                follower, following)

    @classmethod
    def accept_request(cls, follower, following,
            warn_on_unknown = True):

        follower = short_id_to_url(follower)
        following = short_id_to_url(following)

        result = cls._get_follow(follower, following)

        if result is None:

            if warn_on_unknown:
                logger.warn('accepting follow request that we didn\'t know about')

            result = cls(
                    follower = follower,
                    following = following,
                    pending = False,
                    )
        else:
            result.pending = False

        result.save()

        logger.info('%s has started to follow %s: %s',
                follower, following, result)

        return result

    @classmethod
    def reject_request(cls, follower, following):

        follower = short_id_to_url(follower)
        following = short_id_to_url(following)

        if f is None:
            logger.warn('rejecting follow request; '+
                'that\'s fine because we didn\'t know about it')
        else:
            f.delete()

        logger.info('%s was rejected as a follower of %s',
                follower, following)


