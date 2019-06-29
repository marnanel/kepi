import logging
import json

logger = logging.getLogger(name='django_kepi')

def _source_property(candidate):
    try:
        c = json.loads(candidate)
    except json.decoder.JSONDecoderError:
        logger.info('Not JSON: %s', candidate)
        return False

    if not isinstance(c, dict):
        logger.info('Not a dict: %s', candidate)
        return False

    if sorted(c.keys())!=['content', 'mediaType']:
        logger.info('Keys need to be mediaType and content: %s', candidate)
        return False

    return True

ACTIVITYPUB_TYPES = {
    # see: https://www.w3.org/TR/activitystreams-vocabulary/

    'Create': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Update': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Delete': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Follow': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Add': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': None,
            'target': 'id',
            },
        'class': 'Activity',
        },

    'Remove': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': None,
            'target': 'id',
            },
        'class': 'Activity',
        },

    'Like': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Undo': {
        'parent': 'Activity',
        'required': {
            'actor': None,
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Accept': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Reject': {
        'parent': 'Activity',
        'required': {
            'actor': 'id',
            'object': 'id',
            'target': None,
            },
        'class': 'Activity',
        },

    'Activity': {
            'parent': 'Object',
            },

    'Object': {
            'parent': None,
            'optional': {
                'source': _source_property,
                },
            },

    'Announce': {
            # aka "boost"
            'parent': 'Object',
            # FIXME what are the required and optional fields?
            'class': 'Activity',
            },

    'Actor': {

            'class': 'Actor',
            },

    'Application': {
            'parent': 'Object',
            'class': 'Actor',
            },

       'Group': {
            'parent': 'Object',
            'class': 'Actor',
            },


   'Organization': {
            'parent': 'Object',
            'class': 'Actor',
            },


   'Person': {
            'parent': 'Object',
            'class': 'Actor',
            },


   'Service': {
            'parent': 'Object',
            'class': 'Actor',
            },


   'Article': {
            'parent': 'Object',
            'class': 'Item',
            },

   'Audio': {
           'parent': 'Document',
            'class': 'Item',
            },


   'Document': {
           'parent': 'Object',
            'class': 'Item',
            },

   'Event': {
           'parent': 'Object',
            'class': 'Item',
            },

   'Image': {
           'parent': 'Document',
            'class': 'Item',
            },


   'Note': {
           # Why isn't it a subclass of Document?
           'parent': 'Object',
            'class': 'Item',
            },

   'Page': {
           # i.e. a web page
           'parent': 'Document',
            'class': 'Item',
            },

   'Place': {
           'parent': 'Object',
            'class': 'Item',
            },

   'Profile': {
           'parent': 'Object',
            'class': 'Actor',
            },

   'Relationship': {
           'parent': 'Object',
            'class': 'Item',
            },

   'Video': {
           'parent': 'Document',
            'class': 'Item',
            },

    }



