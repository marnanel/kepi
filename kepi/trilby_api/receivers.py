# receivers.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

import kepi.trilby_api.signals as kepi_signals
import kepi.trilby_api.models as kepi_models
import kepi.sombrero_sendpub.delivery as sombrero_delivery
from django.dispatch import receiver

##################################################
# Notification handlers

# FIXME these are really similar. Can we refactor?

@receiver(kepi_signals.followed)
def on_follow(sender, **kwargs):

    follow = sender # rename to prevent confusion below

    notification = kepi_models.Notification(
            notification_type = kepi_models.Notification.FOLLOW,
            for_account = follow.following,
            about_account = follow.follower,
            )

    notification.save()

    logger.info('    -- storing a notification: %s',
            notification)

    if follow.following.auto_follow:
        logger.info("    -- sending automatic Accept")

        if isinstance(follow.follower, kepi_models.RemotePerson):
            accept = {
                    'type': 'Accept',
                    'to': [follow.follower.url],
                    'actor': follow.following.url,
                    'object': follow.offer,
                    }

            sombrero_delivery.deliver(
                    activity = accept,
                    sender = follow.following,
                    target_people = [
                        follow.follower,
                        ],
                    )

        follow.offer = None
        follow.save()
    else:
        logger.info("    -- not sending automatic Accept")

@receiver(kepi_signals.liked)
def on_like(sender, **kwargs):

    like = sender # rename to prevent confusion below

    notification = kepi_models.Notification(
            notification_type = kepi_models.Notification.FAVOURITE,
            for_account = like.liked.account,
            about_account = like.liker,
            status = like.liked,
            )

    notification.save()

    logger.info('    -- storing a notification: %s',
            notification)
