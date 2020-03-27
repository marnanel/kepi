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
        ):

    if isinstance(posted_by, TrilbyUser):
        posted_by = posted_by.person

    result = Status(
        remote_url = None,
        account = posted_by,
        content = content,
        )

    result.save()

    return result
