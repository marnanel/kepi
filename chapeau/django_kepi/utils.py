from django.core.serializers.json import DjangoJSONEncoder

def as_json(d,
        indent=2):

    encoder = DjangoJSONEncoder(
        indent=indent,
        sort_keys=True)

    return encoder.encode(d)


