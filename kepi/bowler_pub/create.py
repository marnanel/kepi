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
logger = logging.getLogger(name="kepi")

import kepi.trilby_api.models as trilby_models
import kepi.trilby_api.utils as trilby_utils
import kepi.bowler_pub
import kepi.bowler_pub.utils as bowler_utils
from kepi.sombrero_sendpub.fetch import fetch

def create(message):

    fields = message.fields
    logger.debug('%s: creating from %s',
            message, message.fields)

    if '_' in fields['type']:
        # no types have underscores in their names, and
        # in this module we use the underscore to separate
        # activity type names from object type names

        logger.warn('%s: underscore in type name "%s"; looks dodgy',
                message,
                fields['type'],
                )
        return

    activity_handler_name = 'on_%s' % (
            fields['type'].lower(),
            )

    if activity_handler_name in globals():
        result = globals()[activity_handler_name](message)
        return result

    logger.warn('%s: no handler for %s',
            message,
            activity_handler_name)

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

def _visibility_from_fields(fields):

    def get_set(fields, fieldname):

        result = fields.get(fieldname, [])
        if isinstance(result, list):
            result = set(result)
        else:
            result = set([result])

        try:
            in_object = fields['object'].get(
                    fieldname, [])
            if isinstance(in_object, list):
                result.update(in_object)
            else:
                result.add(in_object)

        except TypeError:
            pass
        except KeyError:
            pass

        return set(result)

    audience = dict([
        (fieldname, get_set(fields, fieldname))
        for fieldname in ['to', 'cc']
        ])

    for group, result in [
            ('to', trilby_utils.VISIBILITY_PUBLIC),
            ('cc', trilby_utils.VISIBILITY_UNLISTED),
            ]:
        for someone in audience[group]:
            if someone in kepi.bowler_pub.PUBLIC_IDS:
                return result

    # default
    return trilby_utils.VISIBILITY_DIRECT

def on_create(message):
    fields = message.fields
    logger.debug('%s: on_create %s', message, fields)

    newborn_fields = fields['object']
    # XXX Can fields['object'] validly be a URL?

    if 'type' not in newborn_fields:
        logger.info("%s: newborn object had no type",
                message)
        return None

    if newborn_fields['type'].title()!='Note':
        logger.info("%s: don't know how to create %s objects",
                message, newborn_fields,
                )
        return None

    poster = trilby_models.Person.lookup(
        name = fields['actor'],
        create_missing_remote = True,
        )

    if 'inReplyTo' in newborn_fields:
        in_reply_to = trilby_models.Status.lookup(
            url = newborn_fields['inReplyTo'],
            )
    else:
        in_reply_to = None

    is_sensitive = False # FIXME
    spoiler_text = '' # FIXME
    language = 'en' # FIXME

    visibility = _visibility_from_fields(fields)

    newbie = trilby_models.Status(
        remote_url = fields['id'],
        account = poster,
        in_reply_to = in_reply_to,
        content = newborn_fields['content'],
        sensitive = is_sensitive,
        spoiler_text = spoiler_text,
        visibility = visibility,
        language = language,
            )

    newbie.save()

    logger.debug('%s: created status %s',
        message,
        newbie,
        )

def on_announce(message):
    fields = message.fields
    logger.debug('%s: on_announce %s', message, fields)

    try:
        if isinstance(fields.get('object', None), dict):
            # We don't trust an object passed to us as part of
            # an Announce, because it generally comes from a
            # different user. So we take the id and go and
            # look it up for ourselves.
            status_url = fields['object']['id']
        else:
            status_url = fields['object']
    except FieldError as fe:
        logger.info("%s: unusable object field: %s",
                message, fe)
        return None

    status = fetch(status_url,
            expected_type = trilby_models.Status,
            )

    if status is None:

        logger.info("%s: attempted to reblog non-existent status %s",
                message, status_url)
        return None

    actor = fetch(fields['actor'],
            expected_type = trilby_models.Person,
            )

    logger.debug('%s: reblogging status %s by %s',
            message, status_url, actor)

    reblog = trilby_models.Status(
            account = actor,
            reblog_of = status,
            )
    reblog.save()

    logger.debug('%s: created reblog: %s',
            message, reblog)

    return reblog
