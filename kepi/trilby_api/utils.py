VISIBILITY_PUBLIC = 'A'
VISIBILITY_UNLISTED = 'U'
VISIBILITY_PRIVATE = 'X'
VISIBILITY_DIRECT = 'D'

VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, 'public'),
        (VISIBILITY_UNLISTED, 'unlisted'),
        (VISIBILITY_PRIVATE, 'private'),
        (VISIBILITY_DIRECT, 'direct'),
        ]

VISIBILITY_HELP_TEXT = "Public (A): visible to anyone.\n"+\
        "Unlisted (U): visible to anyone, but "+\
        "doesn't appear in timelines.\n"+\
        "Private (X): only visible to followers.\n"+\
        "Direct (D): visible to nobody except tagged people.\n"+\
        "\n"+\
        "Additionally, a person tagged in a status can\n"+\
        "always view that status."
