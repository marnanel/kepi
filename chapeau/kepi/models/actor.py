from django.db import models
from django.conf import settings
from . import acobject
import chapeau.kepi.crypto
import logging
import re

logger = logging.getLogger(name='chapeau')

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

    f_publicKey = models.TextField(
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
        if self.privateKey is None and self.f_publicKey is None:

            if not self.is_local:
                logger.warn('%s: Attempt to save remote without key',
                        self.url)
            else:
                logger.info('%s: generating key pair.',
                        self.url)

                key = kepi.crypto.Key()
                self.privateKey = key.private_as_pem()
                self.f_publicKey = key.public_as_pem()
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
        return settings.KEPI['COLLECTION_URL'] % {
                'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                'username': self.id[1:],
                'listname': name,
                }

    def __setitem__(self, name, value):
        if name=='privateKey':
            self.privateKey = value
            logger.info('%s: setting private key to %s',
                    self, self.privateKey)
            self.save()

        elif name=='publicKey':

            from chapeau.kepi.utils import as_json

            self.f_publicKey = as_json(value,
                    indent=None)
            logger.info('%s: setting public key to %s',
                    self, self.f_publicKey)
            self.save()
        else:
            super().__setitem__(name, value)

    def __getitem__(self, name):

        if self.is_local:

            if name in LIST_NAMES:
                return self.list_url(name)
            elif name=='privateKey':
                return self.privateKey
            elif name=='preferredUsername':
                return self.id[1:]
            elif name=='url':
                return self.url
            elif name=='icon':
                return 'https://%(hostname)s/static/defaults/avatar_0.jpg' % {
                    'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                    }
            elif name=='header':
                return 'https://%(hostname)s/static/defaults/header.jpg' % {
                    'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                    }
            elif name=='email':
                # FIXME this is not really the email address!
                return '{}@{}'.format(
                        self.id[1:],
                        settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                        )
            elif name=='feedURL':
                return settings.KEPI['USER_FEED_URLS'].format(
                        username = self.id[1:],
                        hostname = settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                        )

        if name=='publicKey':
            if not self.f_publicKey:
                logger.debug('%s: we have no known public key',
                        self)
                return None

            from json import loads

            result = loads(self.f_publicKey)
            logger.debug('%s: public key is %s',
                    self, result)
            return result

        result = super().__getitem__(name)
        return result

    @property
    def activity_form(self):
        result = super().activity_form

        if 'publicKey' in result:
            result['publicKey'] = {
                'id': self.url + '#main-key',
                'owner': self.url,
                'publicKeyPem': result['publicKey'],
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

        result['endpoints'] = {}
        if 'SHARED_INBOX' in settings.KEPI:
            result['endpoints']['sharedInbox'] = \
                    settings.KEPI['SHARED_INBOX'] % {
           'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                            }

        result['tag'] = []
        result['attachment'] = []

        result['summary'] = '(Kepi user)'

        # default images, for now
        result['icon'] = {
                "type":"Image",
                "mediaType":"image/jpeg",
                "url": 'https://%(hostname)s/static/defaults/avatar_0.jpg' % {
                    'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                    },
                }

        result['image'] = {
                "type":"Image",
                "mediaType":"image/jpeg",
                "url": 'https://%(hostname)s/static/defaults/header.jpg' % {
                    'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                    },
                }

        return result

##############################

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
