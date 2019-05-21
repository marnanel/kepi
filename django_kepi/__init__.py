__title__ = 'django_kepi'
__version__ = '0.0.20'
VERSION = __version__
__author__ = 'Marnanel Thurman'
__license__ = 'GPL-2'
__copyright__ = 'Copyright (c) 2018 Marnanel Thurman'

import logging

logger = logging.getLogger(name='django_kepi')

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

# Decorator
def implements_activity_type(f_type):
    def register(cls):
        # XXX This will do something again later
        pass #register_type(f_type, cls)
        return cls
    return register

class TombstoneException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__()

        self.activity_form = kwargs.copy()
        self.activity_form['type'] = 'Tombstone'

    def __str__(self):
        return str(self.activity_form)


