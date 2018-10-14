__title__ = 'django_kepi'
__version__ = '0.0.19'
VERSION = __version__
__author__ = 'Marnanel Thurman'
__license__ = 'GPL-2'
__copyright__ = 'Copyright (c) 2018 Marnanel Thurman'

import logging
from collections import defaultdict

# XXX this is mastodon-specific; it will be generalised later
ATSIGN_CONTEXT = [
        "https://www.w3.org/ns/activitystreams", 
        "https://w3id.org/security/v1", 
        {
            "schema": "http://schema.org#", 
            "inReplyToAtomUri": "ostatus:inReplyToAtomUri", 
            "movedTo": "as:movedTo", 
            "conversation": "ostatus:conversation", 
            "ostatus": "http://ostatus.org#", 
            "atomUri": "ostatus:atomUri", 
            "featured": "toot:featured", 
            "value": "schema:value", 
            "PropertyValue": "schema:PropertyValue", 
            "sensitive": "as:sensitive", 
            "toot": "http://joinmastodon.org/ns#", 
            "Hashtag": "as:Hashtag", 
            "manuallyApprovesFollowers": "as:manuallyApprovesFollowers", 
            "focalPoint": {
                "@id": "toot:focalPoint", 
                "@container": "@list"
                }, 
            "Emoji": "toot:Emoji"
            }
        ]

logger = logging.Logger('django_kepi')

object_type_registry = defaultdict(list)

def register_type(f_type, handler):
    object_type_registry[f_type].append(handler)

# Decorator
def implements_activity_type(f_type):
    def register(cls):
        register_type(f_type, cls)
        return cls
    return register

def find(identifier, f_type=None):

    if f_type is None:
        f_type = object_type_registry.keys()
    elif not isinstance(f_type, list):
        f_type = [f_type]

    for t in f_type:

        if t not in object_type_registry:
            continue

        for cls in object_type_registry[t]:
            try:
                result = cls.activity_find(url=identifier)
            except cls.DoesNotExist:
                result = None

            if result is not None:
                return result

    return None

def create(fields):

    if 'type' not in fields:
        raise ValueError('objects must have a type')

    t = fields['type']

    if t not in object_type_registry:
        raise ValueError('type {} is unknown'.format(t,))

    for cls in object_type_registry[t]:
        result = cls.activity_create(fields)

    return result

class TombstoneException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.activity_form = kwargs.copy()
        self.activity_form['type'] = 'Tombstone'

    def __str__(self):
        return str(self.activity_form)


