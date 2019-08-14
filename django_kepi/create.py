# create.py
#
# Part of kepi, an ActivityPub daemon and library.
# Copyright (c) 2018-2019 Marnanel Thurman.
# Licensed under the GNU Public License v2.

"""
This module contains create(), which creates objects.
"""

from django_kepi.models import *
import django.db.utils
import logging

logger = logging.getLogger(name='django_kepi')

def create(
        is_local_user=True,
        run_side_effects=True,
        run_delivery=True,
        value=None,
        **kwargs):

    """
    Creates a kepi object.

    Keyword arguments:
    value -- the fields of the new object, as a dict.
        Must contain a key "type".
    is_local_user -- True if the object is being created by a
        local user, False if we received it across the network.
    run_side_effects -- whether the new object should cause
        its usual side effects. For example, creating a Delete
        object should have the side-effect of deleting something.
    run_delivery -- whether we should attempt to deliver the
        new object to whatever audiences it lists.

    Any extra keyword arguments are taken to be fields of the
    new object, just as if they had appeared in "value".
    Any of these keywords may be prefixed with "f_" to avoid
    confusing Python's parser. For example, you could write
        f_type = "Create"
    to set the "type" field to "Create".

    Don't confuse create() with objects of type Create!
    """

    from django_kepi.delivery import deliver

    if value is None:
        value = {}

    # Remove the "f_" prefix, which exists so that we can write
    # things like f_type or f_object without using reserved keywords.
    for k,v in kwargs.items():
        if k.startswith('f_'):
            value[k[2:]] = v
        else:
            value[k] = v

    logger.info("Create begins: source is %s; local? %s; run side effects? %s",
        value, is_local_user, run_side_effects)

    if value is None:
        logger.warn("  -- it's ludicrous to create an Object with no value")
        return None

    # Now, let's fix the types of keys and values.

    if 'type' not in value:
        logger.warn("Objects must have a type; dropping message")
        return None

    value['type'] = value['type'].title()

    for k,v in value.copy().items():
        if not isinstance(k, str):
            logger.warn('Objects can only have keys which are strings: %s',
                    str(k))
            del value[k]

    if 'id' in value:
        if is_local_user:
            logger.warn('Removing "id" field at local Object creation')
            del value['id']
    else:
        if not is_local_user:
            logger.warn("Remote Objects must have an id; dropping message")
            return None

    try:
        import django_kepi.models as kepi_models
        cls = getattr(locals()['kepi_models'], value['type'])
    except AttributeError:
        logger.warn("There's no type called %s",
                value['type'])
        return None
    except KeyError:
        logger.warn("The class '%s' wasn't exported properly. "+\
                "This shouldn't happen.",
                value['type'])
        return None

    logger.debug('Class for %s is %s', value['type'], cls)
    del value['type']

    if 'url' in value and 'remote_url' in value:
        if value['url']!=value['remote_url']:
            logger.warn('url and remote_url differ (%s vs %s)',
                    value['url'], value['remote_url'])

        # in either case there's no point in keeping url around
        del value['url']

    if 'id' in value and 'url' in value:
        if value['id']!=value['url']:
            logger.warn('id and url differ (%s vs %s)',
                    value['id'], value['url'])
        del value['url']

    ########################

    # Right, we need to create an object.

    if 'id' in value:
        try:
            result = cls(
                    remote_url = value['id'],
                    )
            del value['id']
            result.save()
            logger.warn('  -- created local copy of remote object %s '+\
                    '(url was %s)',
                result, result.remote_url)
        except django.db.utils.IntegrityError:
            logger.warn('We already have an object with remote_url=%s',
                value['id'])
            return None
    else:
        result = cls(
                )
        result.save()
        logger.warn('  -- created local object %s',
            result)

    for f,v in value.items():
        try:
            result[f] = v
        except django.db.utils.Error as pe:
            logger.warn('Can\'t set %s=%s on the new object (%s); bailing',
                f, v, pe)
            return None

    if hasattr(result, '_after_create'):
        result._after_create()

    if run_side_effects:
        success = result.run_side_effects()
        if not success:
            logger.debug('  -- deleting original object')
            try:
                # FIXME This fails because "delete" is a type name!
                result.delete()
            except:
                logger.debug('    -- deletion failed; marking inactive')
                result.active = False
                result.save()
            return None

    if run_delivery:
        deliver(result.number,
                incoming = True)

    return result

