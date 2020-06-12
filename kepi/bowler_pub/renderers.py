from rest_framework.renderers import JSONRenderer

class ActivityRenderer(JSONRenderer):

    media_type = 'application/activity+json'
