# receivers.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

import kepi.trilby_api.signals as kepi_signals
from django.dispatch import receiver
from kepi.sombrero_sendpub.delivery import deliver

@receiver(kepi_signals.followed)
def on_follow(sender, **kwargs):
    """
    If the Follow event describes a remote person being followed,
    then send them an ActivityPub "Follow" activity message about it.

    The spec for "Follow" is here:
    https://www.w3.org/TR/activitystreams-vocabulary/#dfn-follow
    """
    if sender.following.is_local:
        logger.debug("%s is local; not sending update", sender)
        return

    logger.info("Follow received: %s", sender)

    deliver(
            activity = {
                'type': 'Follow',
                'object': sender.following.url,
                },
            sender = sender.follower,
            target_people = [sender.following],
            )

@receiver(kepi_signals.posted)
def on_posted(sender, **kwargs):
    """
    If the posted event describes a remote person being followed,
    then send them an ActivityPub "Create" activity message about it.

    The spec for "Follow" is here:
    https://www.w3.org/TR/activitystreams-vocabulary/#dfn-create
    """

    if not sender.is_local:
        logger.debug("%s is remote; not notifying remote hosts",
                sender)
        return

    logger.info("%s: status creation received", sender)

    deliver(
            activity = {
                "type": "Create",
                "actor": sender.account.url,
                "object": {
                    "type": "Note",
                    "id": sender.url,
                    "content": sender.content,
                    }
                },
            sender = sender.account,
            target_people = sender.account.followers,
            )

    logger.info("%s: status creation notification delivered",
            sender)
