# receivers.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

import kepi.trilby_api.signals as kepi_signals
import kepi.trilby_api.models as kepi_models
from django.dispatch import receiver

##################################################
# Notification handlers

# FIXME these are really similar. Can we refactor?

@receiver(kepi_signals.followed)
def on_follow(sender, **kwargs):

    notification = kepi_models.Notification(
            notification_type = kepi_models.Notification.FOLLOW,
            for_account = sender.following,
            about_account = sender.follower,
            )

    notification.save()

    logger.info('    -- storing a notification: %s',
            notification)

@receiver(kepi_signals.liked)
def on_like(sender, **kwargs):

    notification = kepi_models.Notification(
            notification_type = kepi_models.Notification.FAVOURITE,
            for_account = sender.liked.account,
            about_account = sender.liker,
            status = sender.liked,
            )

    notification.save()

    logger.info('    -- storing a notification: %s',
            notification)
