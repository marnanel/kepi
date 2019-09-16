from django.test import TestCase
from django_kepi.commandviews import *
from . import create_local_note, create_local_person, create_local_like

class TestCommandView(TestCase):

    def _assertions_for_all_classes(self,
            items, obj):

        self.assertEqual(
                items.get(obj.short_id+'.type'),
                obj['type'],
                )
        self.assertTrue(
                items.get(obj.short_id+'.is_local'),
                )
        self.assertTrue(
                items.get(obj.short_id+'.is_active'),
                )
        self.assertEqual(
                items.get(obj.short_id+'.url'),
                obj.url,
                )

    def _compare_strings(
            comparisons,
            items, obj):

        for c in comparisons:

            if type(c)==tuple:
                ourname, acname = c
            else:
                ourname = acname = c

            self.assertEqual(
                    items.get(user.short_id+'.'+ourname),
                    user[acname],
                    )

    def test_item(self):

        note = create_local_note()

        view = view_for(note)
        items = view.items(0)

        self._assertions_for_all_classes(
                items,
                note,
                )
        
        for f in [
                'content',
                ]:
            self.assertEqual(
                    items.get(note.short_id+'.'+f),
                    note[f],
                    )

    def test_user(self):

        user = create_local_person()

        view = view_for(user)
        items = view.items(0)

        self._assertions_for_all_classes(
                items,
                user,
                )

        for f in [
                'icon',
                'header',
                ]:
            self.assertEqual(
                    items.get(user.short_id+'.'+f),
                    user[f],
                    )

        for ourname, acname in [
                ('username', 'id'),
                ('bio', 'summary'),
                ]:
            self.assertEqual(
                    items.get(user.short_id+'.'+ourname),
                    user[acname],
                    )

        self.assertTrue(
                items.get(user.short_id+'.auto_follow'),
                )

    def test_activity(self):

        activity = create_local_like()

        view = view_for(activity)
        items = view.items(0)

        self._assertions_for_all_classes(
                items,
                activity,
                )

    def test_wrong_type(self):

        view = view_for('This is a string')

        self.assertIsNone(view)
