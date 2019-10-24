from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings

def as_json(d,
        indent=2):

    encoder = DjangoJSONEncoder(
        indent=indent,
        sort_keys=True)

    return encoder.encode(d)

def uri_to_url(uri):
    """
    Turns a URI into a URL by prepending "https://"
    and the configured hostname.
    """
    result = "https://{}{}".format(
            settings.KEPI['LOCAL_OBJECT_HOSTNAME'],
            uri)

    return result

def configured_path(keyname,
        **kwargs):
    """
    Returns a path based on the KEPI settings in
    settings.py and local_config.py.

    If the setting is parameterised, pass the
    parameters in as extra arguments.
    """

    uri = settings.KEPI[keyname] % kwargs
    return uri

def configured_url(keyname,
        **kwargs):
    """
    Same as configured_path(), except it
    passes the result through uri_to_url()
    so it's a full URL.
    """
    return uri_to_url(configured_path(keyname, **kwargs))

def is_short_id(s):
    try:
        return str(s)[0] in '/@'
    except IndexError:
        return False

def short_id_to_url(v):
    """
    If v is a short_id (such as "/1234abcd" or "@alice",
    this transforms it into a URL.

    Otherwise, v is returned unchanged.
    """
    if not is_short_id(v):
        return v

    hostname = settings.KEPI['LOCAL_OBJECT_HOSTNAME']

    if v[0]=='@':
        return configured_url('USER_LINK',
                username = v[1:],
                )
    else:
        return configured_url('OBJECT_LINK',
                number = v[1:],
                )


