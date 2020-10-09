# signals.py
#
# Part of kepi.
# Copyright (c) 2018-2020 Marnanel Thurman.
# Licensed under the GNU Public License v2.

import logging
logger = logging.getLogger(name='kepi')

from django.dispatch import Signal

liked = Signal(
        providing_args=[
            'liker',
            'liked',
            ])

followed = Signal(
        providing_args=[
            'follower',
            'followed',
            ])

unfollowed = Signal(
        providing_args=[
            'follower',
            'followed',
            ])

deleted = Signal(
        providing_args=[
            'url',
            'entombed',
            ])

posted = Signal(
        providing_args=[
            ])

reblogged = Signal(
    )
