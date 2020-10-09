# person.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from polymorphic.models import PolymorphicModel
from django.db import models
from django.db.models.constraints import UniqueConstraint
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import kepi.bowler_pub.crypto as crypto
from kepi.bowler_pub.utils import uri_to_url
import kepi.trilby_api.utils as trilby_utils
import kepi.bowler_pub.utils as bowler_utils
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from urllib.parse import urlparse

class Person(PolymorphicModel):

    @classmethod
    def local_form(cls):
        return LocalPerson

    @classmethod
    def remote_form(cls):
        return RemotePerson

    @property
    def icon_or_default(self):
        if self.icon_image:
            return uri_to_url(self.icon_image)

        which = self.id % 10
        return uri_to_url('/static/defaults/avatar_{}.jpg'.format(
            which,
            ))

    @property
    def header_or_default(self):
        if self.header_image:
            return uri_to_url(self.header_image)

        return uri_to_url('/static/defaults/header.jpg')

    display_name = models.CharField(
            max_length = 255,
            verbose_name='display name',
            help_text = 'Your name, in human-friendly form. '+\
                'Something like "Alice Liddell".',
            )

    publicKey = models.TextField(
            blank=True,
            null=True,
            verbose_name='public key',
            )

    note = models.TextField(
            max_length=255,
            help_text="Your biography. Something like "+\
                    '"I enjoy falling down rabbitholes."',
            default='',
            verbose_name='bio',
            )

    auto_follow = models.BooleanField(
            default=True,
            help_text="If True, follow requests will be accepted automatically.",
            )

    locked = models.BooleanField(
            default=False,
            help_text="If True, only followers can see this account's statuses.",
            )

    language = models.CharField(
            default=settings.KEPI['LANGUAGES'][0],
            max_length=16,
            help_text="The language this user usually posts in. Use an ISO 639 "+\
                    "code, such as 'en' or 'cy'.",
            )

    bot = models.BooleanField(
            default=False,
            help_text="If True, this account is a bot. If False, it's a human.",
            )

    moved_to = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = True,
            help_text="If set, the account has moved away, and "+\
                    "this is where it went."
            )

    @property
    def uri(self):
        # I know this property is called "uri", but
        # this matches the behaviour of Mastodon
        return self.url

    @property
    def following(self):
        return Person.objects.filter(
            rel_followers__follower = self,
            )

    @property
    def fields(self):
        return [] # FIXME

    @property
    def emojis(self):
        return [] # FIXME

########################################

class RemotePerson(Person):

    url = models.URLField(
            max_length = 255,
            unique = True,
            null = True,
            blank = True,
            )

    status = models.IntegerField(
            default = 0,
            choices = [
                (0, 'pending'),
                (200, 'found'),
                (404, 'not found'),
                (410, 'gone'),
                (500, 'remote error'),
                ],
            )

    found_at = models.DateTimeField(
            null = True,
            default = None,
            )

    username = models.CharField(
            max_length = 255,
            null = True,
            blank = True,
            )

    inbox_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    outbox_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    following_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    followers_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    featured_url = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    icon = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    header = models.URLField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            )

    key_name = models.CharField(
            max_length = 255,
            null = True,
            blank = True,
            default = '',
            )

    acct = models.CharField(
            max_length = 255,
            null = True,
            blank = True,
            default = None,
            unique = True,
            )

    created_at = models.DateTimeField(
            null = True,
            default = None,
            )

    icon_image = models.ImageField(
            help_text="A small square image used to identify you.",
            null=True,
            verbose_name='icon',
            blank = True,
            )

    header_image = models.ImageField(
            help_text="A large image, wider than it's tall, which appears "+\
                    "at the top of your profile page.",
            null=True,
            verbose_name='header image',
            blank = True,
            )

    @property
    def is_local(self):
        return False

    def __str__(self):
        if self.url is not None:
            return f'[{self.url}]'
        elif self.acct is not None:
            return f'[{self.acct}]'
        else:
            return '[<empty>]'

    @property
    def hostname(self):
        if self.url is not None:
            return urlparse(self.url).netloc

        if self.acct is not None:
            parts = self.acct.split('@')

            if parts[0]=='':
                # the format was @user@hostname
                parts.pop(0)

            return parts[1]

        return None

    @property
    def followers(self):
        from kepi.sombrero_sendpub.fetch import fetch
        from kepi.sombrero_sendpub.collections import Collection

        class RemotePersonFollowers(object):
            def __init__(self, address):
                logger.debug(
                        "%s RemotePerson: initialising",
                        address,
                        )

                self.collection = None
                self.address = address

            def __iter__(self):
                self.collection = fetch(
                        self.address,
                        Collection,
                        ).__iter__()
                logger.debug(
                        "%s RemotePerson: retrieved collection %s",
                        self.address,
                        self.collection,
                        )

                return self

            def __next__(self):

                logger.debug("%s RemotePerson: finding next follower...",
                        self.address,
                        )

                url = self.collection.__next__()

                logger.debug("%s RemotePerson: next follower is at %s",
                        self.address,
                        url,
                        )

                person = fetch(
                        url,
                        Person,
                        )

                logger.debug("%s RemotePerson:  -- which is %s",
                        url,
                        person,
                        )

                return person

        result = RemotePersonFollowers(
                self.followers_url,
                )

        return result

########################################

class TrilbyUser(AbstractUser):
    """
    A Django user.
    """

    def save(self,
            create_twin = True,
            *args, **kwargs):

        first_time = self.pk is None

        super().save(*args, **kwargs)

        if create_twin and first_time:

            local_person = LocalPerson(
                    local_user = self,
                    )
            local_person.save()

            logger.info('%s: created twin %s',
                self, local_person)

class LocalPerson(Person):

    local_user = models.OneToOneField(
            to = TrilbyUser,
            on_delete = models.CASCADE,
            null = True,
            blank = True,
            )

    created_at = models.DateTimeField(
            default = now,
            )

    privateKey = models.TextField(
            blank=True,
            null=True,
            verbose_name='private key',
            )

    icon_image = models.ImageField(
            help_text="A small square image used to identify you.",
            null=True,
            verbose_name='icon',
            blank = True,
            )

    header_image = models.ImageField(
            help_text="A large image, wider than it's tall, which appears "+\
                    "at the top of your profile page.",
            null=True,
            verbose_name='header image',
            blank = True,
            )

    default_visibility = models.CharField(
            max_length = 1,
            default = trilby_utils.VISIBILITY_PUBLIC,
            choices = trilby_utils.VISIBILITY_CHOICES,
            help_text = "Default visibility.\n\n" +\
                    trilby_utils.VISIBILITY_HELP_TEXT,
            )

    default_sensitive = models.BooleanField(
            default = False,
            )

    @property
    def status(self):
        return 200 # necessarily

    def _generate_keys(self):

        logger.info('%s: generating key pair.',
                self.url)

        key = crypto.Key()
        self.privateKey = key.private_as_pem()
        self.publicKey = key.public_as_pem()

    def __init__(self, *args, **kwargs):

        if 'username' in kwargs and 'local_user' not in kwargs:
            new_user = TrilbyUser(
                    username = kwargs['username'],
                    )
            new_user.save(
                    create_twin = False,
                )

            kwargs['local_user'] = new_user
            del kwargs['username']

            logger.info('created new TrilbyUser: %s',
                new_user)

        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):

        # Various defaults.

        if self.display_name=='':
            self.display_name = self.username

        # Create keys, if we're local and we don't have them.

        if self.privateKey is None and self.publicKey is None:
            self._generate_keys()

        # All good.

        super().save(*args, **kwargs)

    @property
    def username(self):
        return self.local_user.username

    @username.setter
    def username(self, newname):
        self.local_user.username = newname
        self.local_user.save()

    @property
    def is_local(self):
        return True

    @property
    def acct(self):
        return self.local_user.username

    def __str__(self):
        return self.username

    @property
    def url(self):
        return uri_to_url(settings.KEPI['USER_LINK'] % {
                'username': self.local_user.username,
                })

    @property
    def following_count(self):

        import kepi.trilby_api.models as trilby_models

        return trilby_models.Follow.objects.filter(
                follower = self,
                offer = None,
                ).count()

    @property
    def followers_count(self):

        import kepi.trilby_api.models as trilby_models

        return trilby_models.Follow.objects.filter(
                following = self,
                offer = None,
                ).count()

    @property
    def statuses_count(self):

        import kepi.trilby_api.models as trilby_models

        # TODO: not yet tested
        return trilby_models.Status.objects.filter(
                account = self,
                ).count()

    @property
    def key_name(self):
        return self.url + '#main-key'

    def get_outbox_collection(self):
        """
        Returns a QuerySet representing the user's outbox.
        """

        # TODO Parameters to show access level.

        import kepi.trilby_api.models as trilby_models

        result = trilby_models.Status.objects.filter(
                account = self,
                )

        return result

    @property
    def inbox_url(self):
        return uri_to_url(settings.KEPI['USER_INBOX_LINK'] % {
                'username': self.local_user.username,
                })

    @property
    def inbox(self):
        """
        Returns a QuerySet representing the user's inbox.

        Your inbox contains:

         - Everything you're tagged in
         - All posts of your own
         - All public posts of your friends
         - All private posts of your mutuals
        """

        import kepi.trilby_api.models as trilby_models

        # tags aren't implemented; FIXME
        everything_youre_tagged_in = trilby_models.Status.objects.none()

        logger.debug("%s.inbox: tagged in: %s",
                self, everything_youre_tagged_in)

        all_your_posts = trilby_models.Status.objects.filter(
                account = self,
                )

        logger.debug("%s.inbox: all your posts: %s",
                self, all_your_posts)

        all_your_friends_public_posts = trilby_models.Status.objects.filter(
                visibility = trilby_utils.VISIBILITY_PUBLIC,
                account__rel_following__following = self,
                )

        logger.debug("%s.inbox: all friends' public: %s",
                self, all_your_friends_public_posts)

        all_your_mutuals_private_posts = trilby_models.Status.objects.filter(
                visibility = trilby_utils.VISIBILITY_PRIVATE,
                account__rel_following__following = self,
                account__rel_followers__follower = self,
                )

        logger.debug("%s.inbox: all mutuals' private: %s",
                self, all_your_mutuals_private_posts)

        result = everything_youre_tagged_in.union(
                all_your_posts,
                all_your_friends_public_posts,
                all_your_mutuals_private_posts,
                )

        return result

    @property
    def followers(self):
        return Person.objects.filter(
            rel_following__following = self,
            )

    @property
    def inbox_url(self):
        return uri_to_url(settings.KEPI['USER_INBOX_LINK'] % {
            'username': self.local_user.username,
            })

    @property
    def outbox_url(self):
        return uri_to_url(settings.KEPI['USER_OUTBOX_LINK'] % {
            'username': self.local_user.username,
            })

    @property
    def featured_url(self):
        return uri_to_url(settings.KEPI['USER_FEATURED_LINK'] % {
            'username': self.local_user.username,
            })

    @property
    def following_url(self):
        return uri_to_url(settings.KEPI['USER_FOLLOWING_LINK'] % {
            'username': self.local_user.username,
            })

    @property
    def followers_url(self):
        return uri_to_url(settings.KEPI['USER_FOLLOWERS_LINK'] % {
            'username': self.local_user.username,
            })
