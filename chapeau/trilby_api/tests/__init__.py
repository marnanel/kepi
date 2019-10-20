def create_local_trilbyuser(name='jemima'):

    from chapeau.kepi.tests import create_local_person
    from chapeau.trilby_api.models import TrilbyUser

    person = create_local_person(name=name)

    result = TrilbyUser(
            username = name,
            actor = person)
    result.save()

    return result
