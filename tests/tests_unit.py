from django.test import TestCase, Client
from django_kepi.models import Create, Like, Update
from things_for_testing.models import ThingUser, ThingArticle

class UserTests(TestCase):

    def test_create(self):

        actor = ThingUser(
                name='Dijkstra',
                )
        actor.save()

        article = ThingArticle(
                title='Go To statement considered harmful',
                )
        article.save()

        activity = Create(
                actor=actor,
                fobject=article,
                )
        activity.save()

        #raise ValueError(str(activity.serialize()))

    def test_update(self):

        actor = ThingUser(
                name='Dijkstra',
                )
        actor.save()

        article = ThingArticle(
                title='Go To statement considered harmful',
                )
        article.save()

        activity = Create(
                actor=actor,
                fobject=article,
                )
        activity.save()

        article2 = ThingArticle(
                title='Actually I rather like spaghetti code',
                )
        article2.save()

        activity = Update(
                actor=actor,
                fobject=article2,
                )
        activity.save()

        #raise ValueError(str(activity.serialize()))

    def test_delete(self):

        actor = ThingUser(
                name='Dijkstra',
                )
        actor.save()

        article = ThingArticle(
                title='Go To statement considered harmful',
                )
        article.save()

        activity = Create(
                actor=actor,
                fobject=article,
                )
        activity.save()

        delete = Update(
                actor=actor,
                fobject=article,
                )
        delete.save()

        # fetch by object ID (we can't do this atm) will get Tombstone

        #raise ValueError(str(activity.serialize()))

    def test_like(self):

        liker = ThingUser(
                name='Uncle Bulgaria',
                )
        liker.save()

        author = ThingUser(
                name='Dijkstra',
                )
        author.save()

        article = ThingArticle(
                title='Go To statement considered harmful',
                )
        article.save()

        create = Create(
                actor=author,
                fobject=article,
                )
        create.save()

        like = Like(
                actor=liker,
                fobject=article,
                )
        like.save()

        raise ValueError(like.serialize_as_str())
