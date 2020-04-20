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

reblogged = Signal(
    )
