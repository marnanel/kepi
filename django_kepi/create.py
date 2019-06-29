from django_kepi.models import *
import django_kepi.types as types
import logging
import json

TYPES = {
        #          actor  object  target
        'Create': (True,  True,   False),
        'Update': (True,  True,   False),
        'Delete': (True,  True,   False),
        'Follow': (True,  True,   False),
        'Add':    (True,  False,  True),
        'Remove': (True,  False,  True),
        'Like':   (True,  True,   False),
        'Undo':   (False, True,   False),
        'Accept': (True,  True,   False),
        'Reject': (True,  True,   False),
        }

logger = logging.getLogger(name='django_kepi')

def create(
        sender=None,
        run_side_effects=True,
        **value):

    # Remove the "f_" prefix, which exists so that we can write
    # things like f_type or f_object without using reserved keywords.
    for k,v in value.copy().items():
        if k.startswith('f_'):
            value[k[2:]] = v
            del value[k]

    # Now, let's fix the types of keys and values.

    for k,v in value.copy().items():
        if not isinstance(k, str):
            logger.warn('Things can only have keys which are strings: %s',
                    str(k))
            continue

        value[k] = _normalise_type_for_thing(v)

    if 'type' not in value:
        logger.warn("Things must have a type; dropping message")
        return

    value['type'] = value['type'].title()

    if 'id' in value:
        if sender is None:
            logger.warn('Removing "id" field at Thing creation')
            del value['id']
    else:
        if sender is not None:
            logger.warn("Remote things must have an id; dropping message")
            return

    record_fields = {
            'active': True,
            }
    other_fields = value.copy()

    try:
        type_spec = types.ACTIVITYPUB_TYPES[value['type']]
    except KeyError:
        logger.info('Unknown thing type: %s; dropping message',
                value['type'])
        return None

    if 'class' not in type_spec:
        logger.info('Type %s can\'t be instantiated',
                value['type'])
        return None

    try:
        cls = globals()[type_spec['class']]
    except KeyError:
        # shouldn't happen!
        logger.warn("The class '%s' wasn't imported into create.py",
                type_spec['class'])
        return None

    logger.debug('Class for %s is %s', value['type'], cls)

    # XXX get the record from "types", and see what fields we need

    try:
        need_actor, need_object, need_target = TYPES[value['type']]
    except KeyError:
        # XXX This will be much more easy when django_kepi.types is
        # XXX working
        if value['type'] in thing.OTHER_OBJECT_TYPES:
            need_actor = need_object = need_target = False
        else:
            logger.warn('Unknown thing type: %s; dropping message',
                    value['type'])
            return

        # XXX We don't currently allow people to create Tombstones here,
        # but we should.

    if need_actor!=('actor' in value) or \
            need_object!=('object' in value) or \
            need_target!=('target' in value):

                def params(a, o, t):
                    result = []
                    if a: result.append('actor')
                    if o: result.append('object')
                    if t: result.append('target')

                    if not result:
                        return 'none'

                    return '+'.join(result)

                we_have = params(
                        'actor' in value,
                        'object' in value,
                        'target' in value,
                        )

                we_need = params(
                        need_actor,
                        need_object,
                        need_target,
                        )

                message = 'Wrong parameters for thing type {}: we have {}, we need {}'.format(
                    value['type'], we_have, we_need)
                logger.warn(message)
                raise ValueError(message)

    # Right, we need to create some objects.
    # Everything in "value" needs to go into:
    #    - a Thing, containing records such as "type",
    #    - zero or more Audiences, for "to" etc
    #    - zero or more ThingFields, for everything else

    for f,v in value.items():
        if f in [
                'actor',
                'name',
                'type',
                ]:
            record_fields['f_'+f] = v
            del other_fields[f]

    if 'id' in value:
        record_fields['remote_url'] = value['id']

    for f in ['id', 'type', 'actor', 'name']:
        if f in other_fields:
            del other_fields[f]

    result = cls(**record_fields)
    result.save()
    logger.debug('Created %s (%s): ----',
            result.f_type,
            result.f_name,
            )

    for f, v in other_fields.items():

        if f in audience.AUDIENCE_FIELD_NAMES:
            audience.Audience.add_audiences_for(
                thing = result,
                field = f,
                value = v,
                )
        else:
            value = json.dumps(v, sort_keys=True)
            n = thing.ThingField(
                    parent = result,
                    name = f,
                    value = value,
                    )
            n.save()
            logger.debug('  -- %s', n)

    for f,v in [
            ('actor', result.f_actor),
            ('url', result.url),
            ]:
        if v:
            logger.debug('  -- [%s %12s %s]',
                    result.number, f, v)

    if run_side_effects:
        result.send_notifications()

    return result

def _normalise_type_for_thing(v):
    logger.debug('Normalising %s', v)

    if v is None:
        return v # we're good with nulls
    if isinstance(v, str):
        return v # strings are fine
    elif isinstance(v, dict):
        return v # so are dicts
    elif isinstance(v, bool):
        return v # also booleans
    elif isinstance(v, list):
        return v # and lists as well
    elif isinstance(v, Thing):
        return v.url # Things can deal with themselves

    # okay, it's something weird

    try:
        return v.activity_form
    except AttributeError:
        return str(v)

