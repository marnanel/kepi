from django_kepi.models import *
import logging

logger = logging.getLogger(name='django_kepi')

def create(
        is_local_user=True,
        run_side_effects=True,
        run_delivery=True,
        value=None,
        **kwargs):

    from django_kepi.delivery import deliver

    if value is None:
        value = kwargs.copy()

    logger.info("Create begins: source is %s; local? %s; run side effects? %s",
        value, is_local_user, run_side_effects)

    if value is None:
        logger.warn("  -- it's ludicrous to create an Object with no value")
        return None

    # Remove the "f_" prefix, which exists so that we can write
    # things like f_type or f_object without using reserved keywords.
    for k,v in kwargs.copy().items():
        if k.startswith('f_'):
            value[k[2:]] = v
            del value[k]

    # Now, let's fix the types of keys and values.

    for k,v in value.copy().items():
        if not isinstance(k, str):
            logger.warn('Objects can only have keys which are strings: %s',
                    str(k))
            continue

    if 'type' not in value:
        logger.warn("Objects must have a type; dropping message")
        return None

    value['type'] = value['type'].title()

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
    except KeyError:
        # shouldn't happen!
        logger.warn("The class '%s' wasn't exported properly",
                type_spec['class'])
        return None

    logger.debug('Class for %s is %s', value['type'], cls)
    del value['type']

    ########################

    # Right, we need to create an object.

    result = cls()

    if 'id' in value:
        result.remote_url = value['id']
        del value['id']

    for f,v in value.items():
        result[f] = v

    if hasattr(result, '_after_create'):
        result._after_create()

    result.save()

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

