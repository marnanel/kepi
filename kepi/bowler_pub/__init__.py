ATSIGN_CONTEXT = "https://www.w3.org/ns/activitystreams"

PUBLIC_IDS = set([
        'https://www.w3.org/ns/activitystreams#Public',
        'as:Public',
        'Public',
        ])

URL_REGEXP = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'
LOCAL_NUMBER_REGEXP = r'/[0-9A-Fa-f]{8}'

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
