import logging
from django.conf import settings

logger = logging.getLogger(name='django_kepi')

def _embellish_Note(thing, user=None):

    if 'summary' not in thing:
        thing['summary'] = None
    if 'sensitive' not in thing:
        thing['sensitive'] = False
    if 'attachment' not in thing:
        thing['attachment'] = []
    if 'tag' not in thing:
        thing['tag'] = []
    if 'to' not in thing:
        thing['to'] = ['https://www.w3.org/ns/activitystreams#Public']
    if 'cc' not in thing:
        thing['cc'] = [user.activity_followers]
    if 'attributedTo' not in thing:
        thing['attributedTo'] = user.activity_id

    ## Conversation structure

    if 'inReplyTo' not in thing:
        thing['inReplyTo'] = None

    ## Content map

    if 'contentMap' not in thing and 'content' in thing:
        thing['contentMap'] = {
                settings.LANGUAGE_CODE: thing['content'],
                }
    elif 'content' not in thing and 'contentMap' in thing:
        # just pick one
        thing['content'] = thing['contentMap'].values()[0]

    ## Atom feeds

    if 'atomUri' not in thing:
        thing['atomUri'] = thing['url']
    if 'inReplyToUri' not in thing:
        thing['inReplyToAtomUri'] = thing['inReplyTo']

    ## All done

    return thing

def embellish(thing, user=None):

    if 'type' not in thing:
        logger.debug('embellish: object does not contain a type: %s',
                str(thing))
        raise ValueError('object does not contain a type!')

    f_type = thing['type']
    logger.debug('embellish: received thing of type %s', f_type)

    ###### general embellishments

    if 'id' not in thing:
        logger.debug('embellish: object does not contain a type: %s',
                str(thing))
        raise ValueError('object does not contain an id!')

    if 'url' not in thing:
        thing['url'] = thing['id']

    # XXX 'published' date: format?

    ###### special embellishments per "type"

    if f_type=='Note':
        thing = _embellish_Note(thing, user)
    else:
        logger.warn('don\'t know how to embellish things of type %s',
                f_type)

    return thing
