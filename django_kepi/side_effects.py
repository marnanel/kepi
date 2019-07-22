import logging
from django_kepi.find import find
from django_kepi.delivery import deliver
from django_kepi.types import ACTIVITYPUB_TYPES

logger = logging.getLogger(name='django_kepi')

def accept(activity):

    obj = activity['object__obj']

    if obj['type']!='Follow':
        logger.warn('Object %s was Accepted, but it isn\'t a Follow',
            obj)
        return False

    logger.debug(' -- follow accepted')

    django_kepi.models.following.accept(
            follower = obj['actor'],
            following = activity['actor'],
            )

    return True

def follow(activity):

    local_user = find(activity['object'], local_only=True)
    remote_user = find(activity['actor'])

    if local_user is not None and local_user.auto_follow:
        logger.info('Local user %s has auto_follow set; must Accept',
                local_user)
        django_kepi.models.following.accept(
                follower = activity['actor'],
                following = activity['object'],
                # XXX this causes a warning; add param to disable it
                )

        from django_kepi.create import kepi_create
        accept_the_request = kepi_create(
                f_to = remote_user.url,
                f_type = 'Accept',
                f_actor = activity['object'],
                f_object = activity.url,
                run_side_effects = False,
                )

        deliver(accept_the_request.number)

    else:
        django_kepi.models.Following.request(
                follower = activity['actor'],
                following = activity['object'],
                )

    return True

def reject(activity):
    obj = activity['object__obj']

    if obj['type']!='Follow':
        logger.warn('Object %s was Rejected, but it isn\'t a Follow',
            obj)
        return False

    logger.debug(' -- follow rejected')

    django_kepi.models.following.reject(
            follower = obj['actor'],
            following = activity['actor'],
            )

    return True

def create(activity):
    from django_kepi.create import create as kepi_create

    raw_material = dict([('f_'+f, v)
        for f,v in activity['object'].items()])

    if 'f_type' not in raw_material:
        logger.warn('Attempt to use Create to create '+\
                'something without a type. '+\
                'Deleting original Create.')

        return False

    if raw_material['f_type'] not in ACTIVITYPUB_TYPES:
        logger.warn('Attempt to use Create to create '+\
                'an object of type %s, which is unknown. '+\
                'Deleting original Create.',
                raw_material['f_type'])

        return False

    if 'class' not in ACTIVITYPUB_TYPES[raw_material['f_type']]:
        logger.warn('Attempt to use Create to create '+\
                'an object of type %s, which is abstract. '+\
                'Deleting original Create.',
                raw_material['f_type'])

        return False

    if ACTIVITYPUB_TYPES[raw_material['f_type']]['class']=='Activity':
        logger.warn('Attempt to use Create to create '+\
                'an object of type %s. '+\
                'Create can only create non-activities. '+\
                'Deleting original Create.',
                raw_material['f_type'])

        return False

    if raw_material.get('attributedTo',None)!=activity['actor']:
        logger.warn('Attribution on object is %s, but '+\
                'actor on Create is %s; '+\
                'fixing this and continuing',
                raw_material.get('attributedTo', None),
                activity['actor'],
                )

    raw_material['attributedTo'] = activity['actor']

    # XXX and also copy audiences, per
    # https://www.w3.org/TR/activitypub/ 6.2

    creation = kepi_create(**raw_material,
            is_local = activity.is_local,
            run_side_effects = False)
    activity['object'] = creation
    activity.save()

    return True

def update(activity):

    new_object = activity['object']

    if 'id' not in new_object:
        logger.warn('Update did not include an id.')
        activity.delete()
        return False

    existing = find(new_object['id'],
            local_only = True)

    if existing is None:
        logger.warn('Update to non-existent object, %s.',
                new_object['id'])
        activity.delete()
        return False

    if existing['attributedTo']!=activity['actor']:
        logger.warn('Update by %s to object owned by %s. '+\
                'Deleting update.',
                activity['actor'],
                existing['attributedTo'],
                )
        activity.delete()
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
