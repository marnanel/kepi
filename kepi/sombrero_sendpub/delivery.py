# delivery.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from celery import shared_task
import requests
import json
import httpsig
import random
from django.http.request import HttpRequest
from django.conf import settings
from urllib.parse import urlparse
from kepi.bowler_pub.utils import *
import datetime
import pytz

def _rfc822_datetime(when=None):
    """
    Formats a datetime to the RFC822 standard.

    (The standard is silly, because GMT should be UTC,
    but we have to use it anyway.)
    """
    if when is None:
        when = datetime.datetime.utcnow()
    else:
        when.replace(tzinfo=pytz.UTC)

    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %T GMT")

class _Postie(object):

    def __init__(self,
            message,
            sender,
            ):

        self.message = message.content
        self.sender = sender
        self.signer = None
        self.sent_to = set()
        self.sent_to_local = False

    def send_to(self, inbox):

        from kepi.bowler_pub import PUBLIC_IDS

        if not inbox:
            logger.debug("Not sending to nobody: %s", inbox)
            return

        if inbox in PUBLIC_IDS:
            logger.debug("Not sending to public: %s", inbox)
            return

        if is_local(inbox):
            if self.sent_to_local:
                logger.debug("Not re-sending to local inbox: %s",
                        inbox)
                return

            logger.debug("Sending to local inbox: %s", inbox)

            _deliver_local(
                    message=self.message,
                    )

            self.sent_to_local = True
            return

        if inbox in self.sent_to:
            logger.debug("Not re-sending to remote inbox: %s", inbox)
            return

        logger.info("Sending to remote inbox: %s", inbox)
        parsed_target_url = urlparse(inbox)

        headers = {
                'Date': _rfc822_datetime(),
                'Host': parsed_target_url.netloc,
                # lowercase is deliberate, to work around
                # an infelicity of the signer library
                'content-type': "application/activity+json",
                }

        if self.signer is None and self.sender is not None:
            self.signer = _signer_for_localperson(
                    localperson = self.sender,
                    )

        if self.signer is not None:
            headers = self.signer.sign(
                    headers,
                    method = 'POST',
                    path = parsed_target_url.path,
                    )

        logger.debug('  -- headers are %s', headers)

        _deliver_remote(
                message=self.message,
                recipient=inbox,
                signer=self.signer,
                )

        # Even if _deliver_remote fails, we continue here.
        # If we've failed once to deliver, we don't
        # want to hammer on the remote server.

        self.sent_to.add(inbox)

def _signer_for_localperson(localperson):

    """
    Given a LocalPerson, return an httpsig.HeaderSigner object which can
    sign headers for them.
    """

    if localperson is None:
        logger.info('not signing outgoing messages because we have no known actor')
        return None

    if localperson.privateKey is None:
        logger.warning('not signing outgoing messages because local person %s '+\
                'has no private key!', localperson)
        return None

    try:
        return httpsig.HeaderSigner(
                key_id=localperson.key_name,
                secret=localperson.privateKey,
                algorithm='rsa-sha256',
                headers=['(request-target)', 'host', 'date', 'content-type'],
                sign_header='signature',
                )
    except httpsig.utils.HttpSigException as hse:
        logger.warning('Local private key was not honoured.')
        logger.warning('This should never happen!')
        logger.warning('Error was: %s', hse)
        logger.warning('Key was: %s', localperson.privateKey)
        return None

def _deliver_local(
        message,
        ):

    """
    Deliver an activity to the shared inbox.

    Keyword arguments:
    message -- the OutgoingActivity we're delivering.
    """

    from kepi.bowler_pub.views.activitypub import InboxView

    class InboxPostRequest(HttpRequest):
        """
        This is a fake HttpRequest.
        """

        def __init__(self):
            super().__init__()

            self.path = '/sharedInbox'
            self.method = 'POST'

    request = InboxPostRequest()

    result = InboxView.as_view()(
        request = request,
        username = None,
        )

    if result.status_code==200:
        logger.debug("Message posted to local /sharedInbox")
    else:
        logger.warning("Message failed to post to local /sharedInbox: error %d",
                result.status_code)

def _deliver_remote(
        message,
        recipient,
        signer,
        ):

    """
    Deliver an activity to a remote actor.

    Keyword arguments:
    message -- the OutgoingActivity we're delivering.
    recipient -- the URL of the recipient
    signer -- an httpsig.HeaderSigner for the
        local actor who sent this activity
    """

    logger.debug('  -- delivering to remote user %s', recipient)

    parsed_target_url = urlparse(recipient)

    headers = {
            'Date': _rfc822_datetime(),
            'Host': parsed_target_url.netloc,
            # lowercase is deliberate, to work around
            # an infelicity of the signer library
            'content-type': "application/activity+json",
            }

    if signer is not None:
        headers = signer.sign(
                headers,
                method = 'POST',
                path = parsed_target_url.path,
                )

    logger.debug('    -- headers are %s', headers)

    # FIXME This is wrong-- we have to look up their inbox address
    # if we don't have it, and post to that

    try:
        response = requests.post(
                recipient,
                data=str(message),
                headers=headers,
                )
    except requests.exceptions.ConnectionError:
        logger.debug('    -- cannot connect')
        return

    logger.debug('    -- posted; server replied: %d %s',
            response.status_code, response.reason)

    if response.status_code>=400 and response.status_code<=499 and \
            (response.status_code not in [404, 410]):

        # The server thinks we made an error. Log the request we made
        # so that we can debug it.

        logger.debug("    -- for debugging: our signer was %s",
                signer.__dict__)
        logger.debug("    -- and this is how the message ran: %s %s",
                headers, message)

@shared_task()
def deliver(
        activity,
        sender,
        target_people = [],
        target_followers_of = [],
        ):

    """
    Deliver an activity to a set of actors.

    Keyword arguments:
        activity -- a dict representing an ActivityPub activity
        sender -- a Person who's doing the sending
        target_people -- list of Person objects who should receive it
        target_followers_of -- list of Person objects whose followers
            should receive it.

    This function is a shared task; it will be run by Celery behind
    the scenes.
    """

    import kepi.sombrero_sendpub.models as sombrero_models

    message = sombrero_models.OutgoingActivity(
            content=json.dumps(activity,
                indent=2,
                ),
            )
    message.save()

    log_one_message(
            direction = "outgoing: "+str(message.pk),
            body = activity,
            )

    signer = None
    postie = _Postie(
            message = message,
            sender = sender,
            )

    for target in target_people:

        logger.debug("outgoing %s: person %s has inbox %s",
                message.pk, target, target.inbox_url)

        postie.send_to(target.inbox_url)

    for following in target_followers_of:

        logger.debug("outgoing %s: sending to person %s's followers...",
                message.pk, following)

        for follower in following.followers:
            logger.debug("outgoing %s:   -- to %s",
                    message.pk, follower)

            postie.send_to(follower.inbox_url)

    logger.debug('outgoing %s: message posted to all inboxes',
        message.pk)
