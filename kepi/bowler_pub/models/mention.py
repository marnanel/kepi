from django.db import models
import logging

logger = logging.getLogger(name='kepi')

######################

class Mention(models.Model):

    from_status = models.ForeignKey(
            'bowler_pub.AcObject',
            on_delete = models.DO_NOTHING,
            )

    to_actor = models.CharField(
            max_length=255,
            )

    def __str__(self):
        return '(%s mentions %s)' % (
                self.from_status,
                self.to_actor,
                )

    @classmethod
    def set_from_tags(cls,
            status,
            tags):

        cls.objects.filter(
                from_status = status,
                ).delete()

        logger.debug('Setting mentions for %s from %s',
                status, tags)

        if not isinstance(tags, list):
            tags = [tags]

        for tag in tags:
            if 'href' not in tag:
                logger.info('No href in mention; ignoring')
                return

            if tag['type']!='Mention':
                continue

            mention = cls(
                    from_status=status,
                    to_actor=tag['href'],
                )
            mention.save()
            logger.debug('  -- created %s',
                    mention)
