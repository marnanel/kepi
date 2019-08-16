# side_effects.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
The functions here are run as side-effects when you
create an object. For example, if you create an object
of type "Delete", then delete() will be run with
the new activity as a parameter.
"""

import logging
from django.conf import settings
from django_kepi.find import find, is_local
from django_kepi.delivery import deliver

logger = logging.getLogger(name='django_kepi')

def accept(activity):

    from django_kepi.models.following import Following

    obj = activity['object__obj']

    if obj['type']!='Follow':
        logger.warn('Object %s was Accepted, but it isn\'t a Follow',
            obj)
        return False

    logger.debug(' -- follow accepted')

    Following.accept_request(
            follower = obj['actor'],
            following = activity['actor'],
            )

    return True

def follow(activity):

    from django_kepi.models.following import Following
    from django_kepi.create import create

    if not is_local(activity['object']):
        logger.info('Following a remote user has no local side-effects.')
        return True

    local_user = find(activity['object'], local_only=True)
    remote_user = find(activity['actor'])

    if local_user is not None and local_user.auto_follow:
        logger.info('Local user %s has auto_follow set; must Accept',
                local_user)

        Following.accept_request(
                follower = activity['actor'],
                following = activity['object'],
                warn_on_unknown = False,
                )

        accept_the_request = create(
                f_to = remote_user.url,
                f_type = 'Accept',
                f_actor = activity['object'],
                f_object = activity.url,
                run_side_effects = False,
                )

        deliver(accept_the_request.number)

    else:
        logger.info('Local user %s does not have auto_follow set.',
                local_user)

        Following.make_request(
                follower = activity['actor'],
                following = activity['object'],
                )

    return True

def reject(activity):

    from django_kepi.models.following import Following

    obj = activity['object__obj']

    if obj['type']!='Follow':
        logger.warn('Object %s was Rejected, but it isn\'t a Follow',
            obj)
        return False

    logger.debug(' -- follow rejected')

    Following.reject_request(
            follower = obj['actor'],
            following = activity['actor'],
            )

    return True

def create(activity):

    import django_kepi.models as kepi_models
    from django_kepi.create import create as kepi_create
    from django_kepi.models.audience import AUDIENCE_FIELD_KEYS

    raw_material = activity['object'].copy()

    f_type = raw_material['type'].title()

    logger.debug('Raw material before adjustments is %s.',
            raw_material)

    for field in AUDIENCE_FIELD_KEYS.union(['attributedTo']):
        # copy audiences, per
        # https://www.w3.org/TR/activitypub/ 6.2
        if field in activity:
            value = activity[field]
            if value:
                raw_material[field] = value

    try:
        if issubclass(getattr(kepi_models,
            f_type),
            kepi_models.Activity):

            logger.warn('Attempt to use Create to create '+\
                    'an object of type %s. '+\
                    'Create can only create non-activities. '+\
                    'Deleting original Create.',
                    f_type)

            return False
    except AttributeError:
        logger.warn('Attempt to use Create to create '+\
                'an object of type %s. '+\
                'I have no idea what that is!',
                f_type)
        return False

    if 'actor' in activity:
        attributedTo = raw_material.get('attributedTo', None)

        if attributedTo!=activity['actor']:
            logger.warn('Attribution on object is %s, but '+\
                    'actor on Create is %s; '+\
                    'fixing this and continuing',
                    attributedTo,
                    activity['actor'],
                    )
            raw_material['attributedTo'] = activity['actor']

    logger.debug('Raw material after adjustments is %s.',
            raw_material)

    def it_is_relevant(something, activity):

        from django_kepi.models import Audience

        logger.debug('Checking whether the new object is relevant to us.')

        for f,v in something.items():
            if (f not in AUDIENCE_FIELD_KEYS) and \
                    f!='attributedTo':
                continue

            if type(v) in [str, bytes]:
                v=[v]

            logger.debug('  -- checking %s, currently %s',
                    f, v)
            for a in v:
                if isinstance(a, Audience):
                    a = a.recipient

                logger.debug('  -- is %s local?', a)
                if is_local(a):
                    logger.debug('    -- yes!')
                    return True

        try:
            tags = something['tag']
            logger.debug('  -- checking mentions; tags are %s',
                    tags)
            for tag in tags:
                if tag['type'].title()!='Mention':
                    continue

                logger.debug('  -- is %s local?', tag['href'])
                if is_local(tag['href']):
                    logger.debug('    -- yes!')
                    return True

        except KeyError:
            logger.debug('  -- failed to find anything out '+\
                    'from the mentions.')

        try:
            inReplyTo = something['inReplyTo']

            logger.debug('  -- checking inReplyTo, currently %s',
                    inReplyTo)

            if find(inReplyTo, local_only=True):
                logger.debug('    -- which is one of ours, so yes')
                return True
        except KeyError:
            logger.debug('  -- failed to find anything out '+\
                    'from inReplyTo.')


        logger.debug('  -- does actor %s have local followers?',
                activity['actor'])
        try:
            if kepi_models.Following.objects.filter(
                    following = activity['actor'],
                    ):
                logger.debug('    -- yes!')
                return True
        except KeyError:
            logger.debug('  -- failed to find anything out '+\
                    'about local followers of actor.')

        logger.debug('  -- no, so it\'s irrelevant.')
        return False

    if not it_is_relevant(raw_material, activity):
        logger.warn('Attempt to use Create to create '+\
                'an object which isn\'t addressed to us. '+\
                'To be honest, that\'s none of our business.')
        return False

    creation = kepi_create(
            value = raw_material,
            is_local_user = activity.is_local,
            run_side_effects = False)
    activity['object'] = creation
    activity.save()

    return True

def update(activity):

    new_object = activity['object']

    if 'id' not in new_object:
        logger.warn('Update did not include an id.')
        return False

    existing = find(new_object['id'],
            local_only = True)

    if existing is None:
        logger.warn('Update to non-existent object, %s.',
                new_object['id'])
        return False

    if existing['attributedTo']!=activity['actor']:
        logger.warn('Update by %s to object owned by %s. '+\
                'Deleting update.',
                activity['actor'],
                existing['attributedTo'],
                )
        return False

    logger.debug('Updating object %s',
            new_object['id'])

    for f, v in sorted(new_object.items()):
        if f=='id':
            continue

        existing[f] = v

    # FIXME if not activity.is_local we have to remove
    # all properties of "existing" which aren't in
    # "new_object"

    existing.save()
    logger.debug('  -- done')

    return True

def delete(activity):

    victim = find(activity['object'],
            local_only = True)

    if victim is None:
        logger.info('  -- attempt to Delete non-existent object.')
        return False

    if settings.KEPI['TOMBSTONES']:
        # I have a lovely cask of amontillado to show you
        victim.entomb()
    else:
        victim.delete()
        logger.info('  -- %s deleted',
                victim)

    return True
