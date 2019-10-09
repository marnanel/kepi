from enum import Enum
from random import randint
from datetime import datetime
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.files.images import ImageFile
from django.conf import settings
from chapeau.trilby_api.crypto import Key
from chapeau.kepi import implements_activity_type

#############################

class Visibility(Enum):
    P = 'public'
    X = 'private'
    U = 'unlisted'
    D = 'direct'

#############################

def iso_date(date):
    return date.isoformat()+'Z'

#############################

def default_avatar(variation=0):
    path = 'defaults/avatar_{0}.jpg'.format(variation%10)

    return ImageFile(
            open(
                StaticFilesStorage().path(path), 'rb')
            )

def default_header():
    path = 'defaults/header.jpg'
    return ImageFile(
            open(
                StaticFilesStorage().path(path), 'rb')
            )

#############################

def avatar_upload_to(instance, filename):
    return 'avatars/%s.jpg' % (
            instance.username,
            )

def header_upload_to(instance, filename):
    return 'headers/%s.jpg' % (
            instance.username,
            )

@implements_activity_type('Person')
@implements_activity_type('Actor')
class Person(models.Model):
    url = models.URLField(max_length=255,
            unique=True)

    @property
    def is_local(self):
        return self.user is not None

    @property
    def activity_id(self):
        return self.url

    @property
    def activity_type(self):
        return 'Person'

    @property
    def activity_form(self):
        if self.user is None:
            return {
                'type': 'Person',
                'id': self.url,
                    }
        else:
            return self.user.activity_form

    @classmethod
    def activity_find(cls, url):
        return self.objects.get(url=url)

    @classmethod
    def activity_create(cls, url):
        raise RuntimeError("you can't create people this way")

class TrilbyUser(AbstractUser):

    REQUIRED_FIELDS = ['username']
    # yes, the USERNAME_FIELD is the email, and not the username.
    # it's an oauth2 thing. just roll with it.
    USERNAME_FIELD = 'email'

    actor = models.OneToOneField(
            Person,
            on_delete=models.CASCADE,
            unique=True,
            null=True,
            )

    username = models.CharField(max_length=255,
            unique=True)

    email = models.EmailField(
            unique=True)

    display_name = models.CharField(max_length=255,
            default='')

    locked = models.BooleanField(default=False)

    note = models.CharField(max_length=255,
            default='')

    linked_url = models.URLField(max_length=255,
            default='')

    moved_to = models.CharField(max_length=255,
            blank=True,
            default='')

    _avatar = models.ImageField(
            upload_to = avatar_upload_to,
            blank=True,
            default=None,
            )

    _header = models.ImageField(
            upload_to = header_upload_to,
            blank=True,
            default=None,
            )

    public_key = models.CharField(
            max_length=255,
            editable = False,
            )

    private_key = models.CharField(
            max_length=255,
            editable = False,
            )

    @property
    def avatar(self):
        if self._avatar is not None:
            return self._avatar
        else:
            return default_avatar(variation=self.pw)

    @property
    def header(self):
        if self._header is not None:
            return self._header
        else:
            return default_header()

    def save(self, *args, **kwargs):

        if not self.private_key:
            key = Key()
            self.private_key = key.private_as_pem()
            self.public_key = key.public_as_pem()

        super().save(*args, **kwargs)

    default_sensitive = models.BooleanField(
            default=False)

    default_visibility = models.CharField(
            max_length = 1,
            choices = [(tag.name, tag.value) for tag in Visibility],
            default = Visibility('public').name,
            )

    def created_at(self):
        # Alias for Django's date_joined. Mastodon calls this created_at,
        # and it makes things easier if the model can call it that too.
        return self.date_joined

    def acct(self):
        # XXX obviously we need to do something else for remote accounts
        return '{0}@{1}'.format(
                self.username,
                settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                )

    def statuses(self):
        return Status.objects.filter(posted_by=self)

    def avatar_static(self):
        # XXX
        return self.avatar

    def header_static(self):
        # XXX
        return self.header

    def updated(self):
        return Status.objects.filter(posted_by=self).latest('created_at').created_at

    ############### Relationship (friending, muting, blocking, etc)

    @property
    def followers(self):
        return TrilbyUser.objects.filter(
                actor__followers__following=self.actor,
                )

    @property
    def following(self):
        return TrilbyUser.objects.filter(
                actor__following__follower=self.actor,
                )

    @property
    def blocking(self):
        return TrilbyUser.objects.filter(
                actor__blockers__blocking=self.actor,
                )

    @property
    def requesting_access(self):
        return TrilbyUser.objects.filter(
                actor__hopefuls__grantor=self.actor,
                )

    def block(self, someone):
        """
        Blocks another user. The other user should
        henceforth be unaware of our existence.
        """
        blocking = kepi.models.Blocking(
                blocking=self.actor,
                blocked=someone.actor)
        blocking.save()

    def unblock(self, someone):
        """
        Unblocks another user.
        """
        kepi.models.Blocking.objects.filter(
                following=self.actor,
                follower=someone.actor,
                ).delete()

    def is_blocking(self, someone):
        return kepi.models.Blocking.objects.filter(
                blocking=self.actor,
                blocker=someone.actor,
                ).exists()

    def follow(self, someone):
        """
        Follows another user.
        This has the side-effect of unblocking them;
        I don't know whether that's reasonable.

        If the other user's account is locked,
        this will request access rather than following.
        """
        if someone.is_blocking(self):
            raise ValueError("Can't follow: blocked.")

        if someone.locked:
            req = kepi.models.RequestingAccess(
                    hopeful=self.actor,
                    grantor=someone.actor,
                    )
            req.save()
        else:
            following = kepi.models.Following(
                    following=someone.actor,
                    follower=self.actor,
                    )
            following.save()

    def unfollow(self, someone):
        kepi.models.Following.objects.filter(
                following=someone.actor,
                follower=self.actor,
                ).delete()
 
    def is_following(self, someone):
        return kepi.models.Following.objects.filter(
                following=someone.actor,
                follower=self.actor,
                ).exists()
 
    def dealWithRequest(self, someone, accept=False):

        if someone.is_following(self):
            raise ValueError("They are already following you.")

        if not kepi.models.RequestingAccess.objects.filter(
                hopeful=someone.actor,
                grantor=self.actor,
                ).exists():
            raise ValueError("They haven't asked to follow you.")

        if accept:
            following = kepi.models.Following(
                    following=self.actor,
                    follower=someone.actor)
            following.save()

        kepi.models.RequestingAccess.objects.filter(
                hopeful=someone.actor,
                grantor=self.actor,
                ).delete()

    #############################

    def profileURL(self):
        return settings.KEPI['LOCAL_OBJECT_HOSTNAME'] % {
                'hostname': settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                'username': self.username,
                }

    def feedURL(self):
        return settings.KEPI['USER_FEED_URLS'].format(
                username = self.username,
                )

    def activityURL(self):
        return settings.KEPI['USER_ACTIVITY_URLS'].format(
                username = self.username,
                )

    def featuredURL(self):
        return settings.KEPI['USER_FEATURED_URLS'].format(
                username = self.username,
                )

    def followersURL(self):
        return settings.KEPI['USER_FOLLOWERS_URLS'].format(
                username = self.username,
                )

    def followingURL(self):
        return settings.KEPI['USER_FOLLOWING_URLS'].format(
                username = self.username,
                )

    def inboxURL(self):
        return settings.KEPI['USER_INBOX_URLS'].format(
                username = self.username,
                )

    def outboxURL(self):
        return settings.KEPI['USER_OUTBOX_URLS'].format(
                username = self.username,
                )

    def links(self):
        return [
                {
                'rel': 'http://webfinger.net/rel/profile-page',
                'type': 'text/html',
                'href': self.profileURL(),
                },
                {
                'rel': 'http://schemas.google.com/g/2010#updates-from',
                'type': 'application/atom+xml',
                'href': self.feedURL(),
                },
                {
                'rel': 'self',
                'type': 'application/activity+json',
                'href': self.activityURL(),
                },
                {
                'rel': 'http://ostatus.org/schema/1.0/subscribe',
                'template': settings.KEPI['AUTHORIZE_FOLLOW_TEMPLATE'],
                },
               ]

    #############################

#############################

class Status(models.Model):

    class Meta:
        verbose_name_plural = "statuses"

    posted_by = models.ForeignKey(TrilbyUser,
            on_delete = models.CASCADE,
            default = 1, # to pacify makemigrations
            )

    # the spec calls this field "status", confusingly
    content = models.TextField()

    created_at = models.DateTimeField(default=now,
            editable=False)

    in_reply_to_id = models.ForeignKey('self',
            on_delete = models.CASCADE,
            blank = True,
            null = True,
            )

    # XXX Media IDs here, when we've implemented Media

    sensitive = models.BooleanField(default=None)
    # applies to the media, not the text

    spoiler_text = models.CharField(max_length=255, default='',
            blank=True)

    visibility = models.CharField(
            max_length = 1,
            choices = [(tag.name, tag.value) for tag in Visibility],
            default = None,
            )

    idempotency_key = models.CharField(max_length=255, default='',
            blank=True)

    def save(self, *args, **kwargs):
        if self.visibility is None:
            self.visibility = self.posted_by.default_visibility
        if self.sensitive is None:
            self.sensitive = self.posted_by.default_sensitive

        super().save(*args, **kwargs)

    def is_sensitive(self):
        return self.spoiler_text!='' or self.sensitive

    def title(self):
        """
        Returns the title of this status.

        This isn't anything useful, but the Atom feed
        requires it. So we return some vacuous string.
        """ 
        return 'Status by %s' % (self.posted_by.username, )

    def __str__(self):
        return str(self.posted_by) + " - " + self.content

    def _path_formatting(self, formatting):
        return settings.KEPI[formatting].format(
                username=self.posted_by.username,
                id=self.id,
                )

    def url(self):
        return self._path_formatting('STATUS_URLS')

    def uri(self):
        return self.url()

    def emojis(self):
        # I suppose we should do emojis eventually
        return []

    def reblog(self):
        # XXX
        return None

    def reblogs_count(self):
        # XXX change to a ResultSet
        return 0

    def favourites_count(self):
        # XXX change to a ResultSet
        return 0

    def reblogged(self):
        # XXX
        return False

    def favourited(self):
        # XXX
        return False

    def muted(self):
        # XXX
        return False

    def mentions(self):
        # XXX
        return []

    def media_attachments(self):
        # XXX
        return []

    def tags(self):
        # XXX
        return []

    def language(self):
        # XXX
        return 'en'

    def pinned(self):
        # XXX
        return False

    def in_reply_to_account_id(self):
        if self.in_reply_to_id is None:
            return None
        else:
            return self.in_reply_to_id.posted_by.pk

    def application(self):
        # XXX
        return None

    def atomURL(self):
        return self._path_formatting('STATUS_FEED_URLS')

    def activityURL(self):
        return self._path_formatting('STATUS_ACTIVITY_URLS')

    def conversation(self):
        """
        The string ID of the conversation this Status belongs to.

        If we're a reply to another Status, we inherit the
        conversation ID of that Status. Otherwise, we make up
        our own ID, which should be a tag: URL as defined by RFC4151.
        """

        # XXX check in_reply_to

        now = datetime.now()

        return 'tag:%s,%04d-%02d-%02d:objectId=%d:objectType=Conversation' % (
                settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
                now.year,
                now.month,
                now.day,
                self.id,
                )

class MessageCapturer(models.Model):
    received_at = models.DateTimeField(default=now,
            editable=False)

    box = models.CharField(max_length=255)

    content = models.TextField()
    headers = models.TextField()

    def __str__(self):
        return self.content[:100]
