# create.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This contains create(), which creates the appropriate
model instance when we've received an ActivityPub message.

create() is called by validate() when we've validated
the message.
"""

import logging
import kepi.trilby_api.models as trilby_models

logger = logging.getLogger(name='kepi')

def create(message):

    fields = message.fields
    logger.debug('%s: creating from %s',
            message, message.fields)

    handler_name = 'on_'+fields['type'].lower()

    if handler_name not in globals():
        logger.warn('%s: no handler for %s',
                message,
                handler_name)
        return

    result = globals()[handler_name](message)

    return result

def on_follow(message):

    fields = message.fields
    logger.debug('%s: on_follow %s', message, fields)

    follower = trilby_models.Person.lookup(fields['actor'],
            create_missing_remote = True)

    if follower is None:
        # shouldn't happen
        logger.warn('%s: could not find remote user %s',
                message,
                fields['actor'],
                )
        return

    following = trilby_models.Person.lookup(fields['object'])
    if following is None:
        logger.info('%s: there is no local user %s',
                message,
                fields['object'],
                )
        return

    result = trilby_models.Follow(
            follower = follower,
            following = following,
            )

    result.save()
    return result
