import logging
from django.conf import settings
from django_kepi.find import find
from django_kepi.delivery import deliver

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

    from django_kepi.models.following import Following
    from django_kepi.create import create

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

    raw_material = dict([('f_'+f, v)
        for f,v in activity['object'].items()])

    if issubclass(getattr(kepi_models,
        raw_material['f_type']),
        kepi_models.Activity):

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
