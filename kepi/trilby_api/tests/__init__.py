from kepi.trilby_api.models import *

PUBLIC = "https://www.w3.org/ns/activitystreams#Public"

def create_local_person(name='jemima'):

    from kepi.trilby_api.models import TrilbyUser

    user = TrilbyUser(
            username = name,
            )
    user.save()

    result = Person(
            local_user = user,
            )
    result.save()

    return result

def create_local_status(content,
        posted_by,
        to=[PUBLIC],
        ):

    from kepi.bowler_pub.create import create

    if isinstance(posted_by, TrilbyUser):
        posted_by = posted_by.actor

    result = create(
            is_local_user=True,
            run_side_effects=True,
            run_delivery=False,
            incoming=False,
            value={
                'type': 'Create',
                'actor': posted_by.id,
                'object': {
                    'type': 'Note',
                    'attributedTo': posted_by.id,
                    'content': content,
                    },
                'to': to,
            },
            )

    return result['object__obj']
