from django.db import models
from . import acobject, audience
from .. import PUBLIC_IDS
from django.conf import settings
import logging
import random

logger = logging.getLogger(name='kepi')

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

        audiences = audience.Audience.get_audiences_for(self)
        audience_to = set(audiences.get('to', []))
        audience_cc = set(audiences.get('cc', []))

        logger.debug('%s: checking visibility in audiences',
                self.id)
        logger.debug('   To: %s', audience_to)
        logger.debug('   Cc: %s', audience_cc)

        if not audience_to.union(audience_cc):
            logger.debug('  -- neither to nor cc, so direct')
            return 'direct'
        elif PUBLIC_IDS.intersection(audience_to):
            return 'public'
        elif PUBLIC_IDS.intersection(audience_cc):
            return 'unlisted'

        actor = self.actor

        if actor is None:
            logger.debug('%s: posted by %s, whom we don\'t know about',
                    self.id, self.f_attributedTo)
        else:
            logger.debug('%s: checking visibility from poster: %s',
                    self.id, actor)

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

    def __getitem__(self, name):

        if self.is_local:
            if name=='language':
                return settings.LANGUAGE_CODE

        result = super().__getitem__(name)
        return result

    @property
    def text(self):
        return self.f_content

    @property
    def html(self):
        # FIXME obviously we need to quote this and stuff
        return '<p>%s</p>' % (self.f_content,)

    @property
    def thread(self):

        from kepi.bowler_pub.find import find

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
        return self['inReplyTo'] is not None

    @property
    def ancestors(self):
        # FIXME
        return []

    @property
    def descendants(self):
        # FIXME - do they want *all* descendants in *all* threads?
        return []

    @property
    def in_reply_to_account_id(self):
        parent = self['inReplyTo__obj']

        if parent is None:
            return None

        return parent['attributedTo']

    @property
    def actor(self):
        """
        The AcActor who posted this status.

        We might have no AcActor record for the poster,
        in which case this property will be None.
        You can still find the name of the actor in f_attributedTo.
        """
        from kepi.bowler_pub.find import find

        return find(self.f_attributedTo, local_only=True)

    @property
    def account(self):
        return self['attributedTo']

    @property
    def mentions(self):
        from kepi.bowler_pub.models.mention import Mention

        logger.info('Finding Mentions for %s', self)
        return [x.to_actor for x in
                Mention.objects.filter(from_status=self)]

    @property
    def conversation(self):
        # FIXME I really don't understand conversation values
        return None

    @property
    def activity_form(self):
        result = super().activity_form

        result['url'] = result['id']

        # defaults
        for f, default in [
                ('inReplyTo', None),
                ('sensitive', False),
                ('attachment', []),
                ('tag', []),
                ]:
            if f not in result:
                result[f] = default

        if 'content' in result and 'contentMap' not in result:
            result['contentMap'] = {
                    settings.LANGUAGE_CODE: result['content'],
                    }

        return result

    @property
    def language(self):
        return self['language']

    @property
    def sensitive(self):
        # FIXME
        return False

    @property
    def spoiler_text(self):
        # FIXME
        return ''

    @property
    def emojis(self):
        # FIXME
        return []

    @property
    def reblogs_count(self):
        # FIXME
        return 0

    @property
    def favourites_count(self):
        # FIXME
        return 0

    @property
    def reblogged(self):
        return self.reblogs_count!=0

    @property
    def favourited(self):
        return self.favourites_count!=0

    @property
    def muted(self):
        # FIXME
        return False

    @property
    def media_attachments(self):
        # FIXME
        return []

    @property
    def tags(self):
        # FIXME
        return []

    @property
    def card(self):
        return None

    @property
    def poll(self):
        return None

    @property
    def application(self):
        return self['_application']

    @property
    def language(self):
        return self['language']

    @property
    def pinned(self):
        # FIXME
        return False

    @property
    def posted_by(self):
        return self.f_attributedTo

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

    class Meta:
        verbose_name = 'note'

    def __str__(self):

        content = self.f_content

        if len(content)>70:
            content = content[:68]+'...'

        result = '(%s) "%s"' % (
                self.id,
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
