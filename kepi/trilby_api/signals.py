# signals.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.dispatch import Signal

liked = Signal()
unliked = Signal()
followed = Signal()
unfollowed = Signal()
posted = Signal()
reblogged = Signal()
