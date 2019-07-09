from django.db import models
from . import thing, audience
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Item(thing.Thing):

    f_content = models.CharField(
            max_length=255,
            blank=True,
            )

    f_attributedTo = models.CharField(
            max_length=255,
            blank=True,
            )

    @property
    def visibility(self):
        audiences = audience.Audience.get_audiences_for(self)
        logger.debug('%s', str(audiences))

        if audience.PUBLIC in audiences.get('to', []):
            return 'public'
        elif audience.PUBLIC in audiences.get('cc', []):
            return 'unlisted'
        return 'direct'

    @property
    def text(self):
        return self['content']

    @property
    def thread(self):

        from django_kepi.find import find

        if hasattr(self, '_thread'):
            return self._thread

        result = self

        logger.debug('Searching for thread of %s',
                result)

        while True:
            parent = result['inReplyTo']

            if parent is None:
                break

            logger.debug('  -- scanning its parent %s',
                    parent)

            parent = find(
                    parent,
                    do_not_fetch = True)

            if parent is None:
                logger.debug('   -- which is remote and not cached')
                break

            result = parent

        logger.debug('  -- result is %s',
                result)

        self._thread = result

        return result

    @property
    def is_reply(self):
        return 'inReplyTo' in self

    @property
    def in_reply_to_account(self):
        parent = self['inReplyTo__obj']

        if parent is None:
            return None

        return parent['attributedTo']

    @property
    def account(self):
        return self['attributedTo']

    @property
    def mentions(self):
        from django_kepi.models.mention import Mention

        logger.info('Finding Mentions for %s', self)
        return [x.to_actor for x in
                Mention.objects.filter(from_status=self)]

    @property
    def conversation(self):
        # FIXME I really don't understand conversation values
        return None
