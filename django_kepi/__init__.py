__title__ = 'django_kepi'
__version__ = '0.0.16'
VERSION = __version__
__author__ = 'Marnanel Thurman'
__license__ = 'GPL-2'
__copyright__ = 'Copyright (c) 2018 Marnanel Thurman'

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

object_type_registry = {
        }

def register_type(atype, handler):
    object_type_registry[atype] = handler

def resolve(identifier, atype=None):

    if atype is None:
        atype = object_type_registry.keys()
    elif not isinstance(atype, list):
        atype = [atype]

    for t in atype:

        if t not in object_type_registry:
            continue

        result = object_type_registry[t].find_activity(url=identifier)

        if result is not None:
            return result

    return None

class TombstoneException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.activity = kwargs.copy()
        self.activity['type'] = 'Tombstone'

    def __str__(self):
        return str(self.activity)

class NeedToFetchException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.url = kwargs['url']

    def __str__(self):
        return self.url

