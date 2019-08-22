from django.db import models
from . import acobject, audience
from .. import PUBLIC_IDS
import logging

logger = logging.getLogger(name='django_kepi')

######################

class AcItem(acobject.AcObject):

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

        from django_kepi.find import find

        audiences = audience.Audience.get_audiences_for(self)
        logger.debug('%s: checking visibility in audiences: %s',
                self.number, str(audiences))

        audience_to = set(audiences.get('to', []))
        audience_cc = set(audiences.get('cc', []))

        if not audience_to.union(audience_cc):
            logger.debug('  -- neither to nor cc, so direct')
            return 'direct'
        elif PUBLIC_IDS.intersection(audience_to):
            return 'public'
        elif PUBLIC_IDS.intersection(audience_cc):
            return 'unlisted'

        actor = find(self.account, local_only=True)

        if actor is None:
            logger.debug('%s: posted by %s, whom we don\'t know about',
                    self.number, self.account)
        else:
            logger.debug('%s: checking visibility from poster: %s',
                    self.number, actor)

            followers_url = actor['followers']

            logger.debug('  -- is %s in %s?',
                    followers_url, audience_to)

            if followers_url in audience_to:
                logger.debug('    -- yes, so private')
                return 'private'

        # By now, it's either direct or limited.
        # Direct means there's a mention with a
        # recipient's name in it.

        mentions = self.mentions

        logger.debug('  -- is %s in %s?',
                audience_to, mentions)

        if audience_to.intersection(mentions):
            logger.debug('    -- yes, so it\'s direct')
            return 'direct'

        logger.debug('  -- fallback to limited')
        return 'limited'

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
        return set([x.to_actor for x in
                Mention.objects.filter(from_status=self)])

    @property
    def conversation(self):
        # FIXME I really don't understand conversation values
        return None

##############################

class AcArticle(AcItem):
    pass

class AcAudio(AcItem):
    pass

class AcDocument(AcItem):
    pass

class AcEvent(AcItem):
    pass

class AcImage(AcItem):
    pass

class AcNote(AcItem):

    # Why isn't Note a subclass of Document?

    def __str__(self):

        content = self['content']

        if len(content)>70:
            content = content[:68]+'...'

        result = '(%s) "%s"' % (
                self.number,
                content)

        return result

class AcPage(AcItem):
    # i.e. a web page
    pass

class AcPlace(AcItem):
    pass

class AcProfile(AcItem):
    pass

class AcRelationship(AcItem):
    pass

class AcVideo(AcItem):
    pass
