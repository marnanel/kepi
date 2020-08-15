# acobject.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.Logger("kepi")

from polymorphic.models import PolymorphicModel

class AcObject(PolymorphicModel):

    """
    AcObjects are the ancestors of classes we can
    receive over ActivityPub.
    """

    class Meta:
        abstract = True
