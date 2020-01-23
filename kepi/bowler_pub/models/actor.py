from django.db import models
from django.conf import settings
from . import acobject, following, collection
import kepi.bowler_pub.crypto as crypto
from kepi.bowler_pub.utils import configured_url, uri_to_url
import logging
import re

logger = logging.getLogger(name='kepi')

LIST_NAMES = [
'inbox', 'outbox', 'followers', 'following',
]

######################

class AcActor(acobject.AcObject):
    """
    An AcActor is a kind of AcObject representing a person,
    an organisation, a bot, or anything else that can
    post stuff and interact with other AcActors.
    """

    privateKey = models.TextField(
            blank=True,
            null=True,
            )

    f_name = models.TextField(
            verbose_name='name',
            help_text = 'Your name, in human-friendly form. '+\
                'Something like "Alice Liddell".',
            )

    publicKey = models.TextField(
            blank=True,
            null=True,
            verbose_name='public key',
            )

    auto_follow = models.BooleanField(
            default=True,
            help_text="If True, follow requests will be accepted automatically.",
            )

    f_summary = models.TextField(
            max_length=255,
            help_text="Your biography. Something like "+\
                    '"I enjoy falling down rabbitholes."',
            default='',
            verbose_name='bio',
            )

    icon = models.ImageField(
            help_text="A small square image used to identify you.",
            null=True,
            verbose_name='icon',
            )

    header = models.ImageField(
            help_text="A large image, wider than it's tall, which appears "+\
                    "at the top of your profile page.",
            null=True,
            verbose_name='header image',
            )

    def _generate_id(self):
        return None

    def _check_provided_id(self):
        if not re.match(r'@[a-z0-9_-]+$', self.id,
                re.IGNORECASE):
            raise ValueError("Actor IDs begin with an @ "+\
                    "followed by one or more characters from "+\
                    "A-Z, a-z, 0-9, underscore, or hyphen. "+\
                    "You gave: "+self.id)

    def _after_create(self):
        if self.privateKey is None and self.publicKey is None:

            if not self.is_local:
                logger.warn('%s: Attempt to save remote without key',
                        self.url)
            else:
                logger.info('%s: generating key pair.',
                        self.url)

                key = crypto.Key()
                self.privateKey = key.private_as_pem()
                self.publicKey = key.public_as_pem()
                self.save()

    def __str__(self):
        if self.is_local:
            return '[{}]'.format(
                    self.id,
                    )
        else:
            return '[remote user {}]'.format(
                    self.id,
                    )

    @property
    def key_name(self):
        """
        The name of this key.
        """
        return '%s#main-key' % (self.url,)

    def list_url(self, name):
        return configured_url('COLLECTION_LINK',
                username = self.id[1:],
                listname = name,
                )

    def __setitem__(self, name, value):
        if name=='privateKey':
            self.privateKey = value
            logger.info('%s: setting private key to %s',
                    self, self.privateKey)
            self.save()

        elif name=='publicKey':

            from kepi.bowler_pub.utils import as_json

            self.publicKey = as_json(value,
                    indent=None)
            logger.info('%s: setting public key to %s',
                    self, self.publicKey)
            self.save()
        else:
            super().__setitem__(name, value)

    @property
    def icon_or_default(self):
        if self.icon:
            return self.icon

        which = ord(self.id[1]) % 10
        return uri_to_url('/static/defaults/avatar_{}.jpg'.format(
            which,
            ))

    @property
    def header_or_default(self):
        if self.header:
            return self.header

        return uri_to_url('/static/defaults/header.jpg')

    @property
    def acct(self):
        if self.is_local:
            return self.id[1:]
        else:
            # XXX This is wrong, because self.id[] is not
            # the preferredUsername
            return '{}@{}'.format(
                    self['preferredUsername'],
                    self.hostname,
                    )

    @property
    def hostname(self):
        if self.is_local:
            return settings.KEPI['LOCAL_OBJECT_HOSTNAME']
        else:
            from urllib.parse import urlparse
            parsed_url = urlparse(self.url)
            return parsed_url.hostname

    def __getitem__(self, name):

        if self.is_local:

            if name in LIST_NAMES:
                return self.list_url(name)
            elif name=='privateKey':
                return self.privateKey
            elif name in ('preferredUsername', 'username'):
                return self.id[1:]
            elif name=='url':
                return self.url
            elif name=='feedURL':
                return configured_url('USER_FEED_LINK',
                        username = self.id[1:],
                        )
        if name=='publicKey':
            if not self.publicKey:
                logger.debug('%s: we have no known public key',
                        self)
                return None

            from json import loads

            result = loads(self.publicKey)
            logger.debug('%s: public key is %s',
                    self, result)
            return result

        result = super().__getitem__(name)
        return result

    @property
    def activity_form(self):
        result = super().activity_form

        result['publicKey'] = {
            'id': self.url + '#main-key',
            'owner': self.url,
            'publicKeyPem': self.publicKey,
            }

        for listname in LIST_NAMES:
            result[listname] = self.list_url(listname)

        for attribute in [
                'url',
                'preferredUsername',
                ]:
            result[attribute] = self[attribute]

        for delendum in [
                'published',
                ]:
            del result[delendum]

        result['endpoints'] = {
                'sharedInbox': configured_url('SHARED_INBOX_LINK'),
                }

        result['tag'] = []
        result['attachment'] = []

        result['icon'] = {
                "type":"Image",
                "mediaType":"image/jpeg",
                "url": self['avatar'],
                }

        result['image'] = {
                "type":"Image",
                "mediaType":"image/jpeg",
                "url": self['header'],
                }

        return result

    @property
    def moved_to(self):
        return None # TODO

    @property
    def fields(self):
        return [] # FIXME

    @property
    def emojis(self):
        return [] # FIXME

    @property
    def locked(self):
        return False # TODO

    @property
    def default_visibility(self):
        return 'public' # FIXME

    @property
    def default_sensitive(self):
        return False # FIXME

    @property
    def bot(self):
        return False # FIXME

    @property
    def language(self):
        return settings.KEPI['LANGUAGES'][0] # FIXME

    @property
    def preferredUsername(self):
        return self['preferredUsername']

    @property
    def display_name(self):
        if self.is_local:
            return self.f_name
        else:
            return self['display_name']

    @property
    def following_count(self):
        return following.Following.objects.filter(
                follower=self.id,
                pending=False).count()

    @property
    def followers_count(self):
        return following.Following.objects.filter(
                following=self.id,
                pending=False).count()

    @property
    def statuses_count(self):
        return collection.Collection.get(
                user = self,
                collection = 'outbox',
                create_if_missing = True,
                ).members.count()


class AcApplication(AcActor):
    pass

class AcGroup(AcActor):
    pass

class AcOrganization(AcActor):
    pass

class AcPerson(AcActor):
    class Meta:
        verbose_name = 'person'
        verbose_name_plural = 'people'

class AcService(AcActor):
    pass
