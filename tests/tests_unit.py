from django.test import TestCase, Client
from django_kepi.models import Create, Like, Update, Delete, lookup
from things_for_testing.models import ThingUser, ThingArticle
import datetime

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

        create = Create(
                actor=actor,
                fobject=article,
                )
        create.save()

        serialized = create.serialize()

        for field in [
                'id', 'type',
                'object', 'actor',
                'published', 'updated',
                ]:

            self.assertIn(field, serialized)

        self.assertIsInstance(
                serialized['id'],
                str)
        self.assertEqual(
                serialized['type'],
                'Create')
        self.assertDictEqual(
                serialized['object'],
                article.serialize(),
                )
        self.assertEqual(
                serialized['actor'],
                'https://example.com/user/Dijkstra')
        self.assertIsInstance(
                serialized['published'],
                datetime.datetime,
                )
        self.assertIsInstance(
                serialized['updated'],
                datetime.datetime,
                )

        looked_up = lookup('create', create.slug)

        self.assertEqual(
                looked_up,
                create,
                )

    def test_update(self):

        actor = ThingUser(
                name='Dijkstra',
                )
        actor.save()

        article = ThingArticle(
                title='Go To statement considered harmful',
                )
        article.save()

        create = Create(
                actor=actor,
                fobject=article,
                )
        create.save()

        article2 = ThingArticle(
                title='Actually I rather like spaghetti code',
                )
        article2.save()

        update = Update(
                actor=actor,
                fobject=article2,
                )
        update.save()

    def test_delete(self):

        actor = ThingUser(
                name='Dijkstra',
                )
        actor.save()

        article = ThingArticle(
                title='Go To statement considered harmful',
                )
        article.save()

        create = Create(
                actor=actor,
                fobject=article,
                )
        create.save()

        delete = Delete(
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

        #raise ValueError(like.serialize_as_str())
