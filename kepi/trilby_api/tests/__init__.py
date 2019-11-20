from kepi.trilby_api.models import TrilbyUser

PUBLIC = "https://www.w3.org/ns/activitystreams#Public"

def create_local_trilbyuser(name='jemima'):

    from kepi.bowler_pub.tests import create_local_person
    from kepi.trilby_api.models import TrilbyUser

    person = create_local_person(name=name)

    result = TrilbyUser(
            username = name,
            actor = person)
    result.save()

    return result

def create_local_status(content,
        posted_by):

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
                'to': [PUBLIC],
            },
            )

    return result
