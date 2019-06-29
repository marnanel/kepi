from django.db import models
from . import thing
import logging

logger = logging.getLogger(name='django_kepi')

######################

class Item(thing.Thing):
    pass

