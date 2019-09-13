from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_kepi.models import *
from django_kepi.create import create
from django_kepi.management import KepiCommand, objects_by_keywords
import os
import logging
import json

logger = logging.Logger('django_kepi')

class Command(KepiCommand):

    help = 'delete users, statuses, etc'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('id',
                help='the object to delete: @name for a user, or an '+\
                        '8-digit number',
                metavar='OBJECT',
                nargs='+',
                )

        parser.add_argument('--yes',
                help='don\'t ask "are you sure", just do it',
                action='store_true',
                )

        parser.add_argument('--json',
                help='pretty-print the json that would be sent over the wire',
                action='store_true',
                )

    ################################

    def _show_actor(self, somebody, *args, **options):
        self.stdout.write('== %s ==' % (somebody,))
        self.stdout.write('')
        self.stdout.write('URL: %s' % (somebody.url,))
        self.stdout.write('Bio: %s' % (somebody.f_summary,))

        followers = Following.objects.filter(
                following = somebody,
                )
        following = Following.objects.filter(
                follower = somebody,
                )
        self.stdout.write('Followers: %d.  Following: %d.  Auto-follow? %s' % (
            followers.count(),
            following.count(),
            somebody.auto_follow,))

        statuses = AcItem.objects.filter_local_only(
                f_attributedTo = somebody.url,
                )

        self.stdout.write('Statuses: %d' % (statuses.count(),))
        for status in statuses:
            self.stdout.write('  (%s) %s' % (status.number, status.f_content,))

    def _show_activity(self, activity, *args, **options):
        print('== activity %s ==' % (activity.number,))

        print('Type: %s' % (activity.f_type,))
        print('Actor: %s' % (activity['actor'],))
        print('Object: %s' % (activity['object'],))
        print('Target: %s' % (activity['target'],))

    def _show_item(self, item, *args, **options):
        print('== item %s ==:' % (item.number,))

        # XXX date etc
        # XXX find activity which created it
        # XXX audiences; also, direct/public/whatever
        print('By: %s' % (item['attributedTo'],))
        print('Content: %s' % (item['content'],))

    def _show_raw_object(self, thing, *args, **options):
        for f,v in sorted(thing.activity_form.items()):
            print('%s: %s' % (
                    f, v,)
                    )

    def _show_json(self, thing, *args, **options):

        print(json.dumps(
            thing.activity_form,
            indent=2,
            sort_keys=True))

    ################################

    def _show_thing(self, thing, *args, **options):

        if options['raw']:
            self._show_raw_object(thing, *args, **options)
        elif options['json']:
            self._show_json(thing, *args, **options)
        elif isinstance(thing, AcActor):
            self._show_actor(thing, *args, **options)
        elif isinstance(thing, AcActivity):
            self._show_activity(thing, *args, **options)
        elif isinstance(thing, AcItem):
            self._show_item(thing, *args, **options)
        else:
            self._show_raw_object(thing, *args, **options)

    ################################

    def handle(self, *args, **options):

        super().handle(*args, **options)

        try:
            things = objects_by_keywords(options['id'])
            logger.info('Requesting deletion of %s, which give %s',
                    name, things)
        except KeyError as ke:
            self.stdout.write(self.style.ERROR(
                ke.args[0],))
            logger.info('Requesting deletion of %s failed: %s',
                    name, ke.args[0])
            return

        if not options['yes']:
            print('About to delete:')
            for thing in things:
                print('  %s' % (thing,))

            logger.debug('Asking user "are you sure?"')
            ays = input('Delete: are you sure? (y/n) ')

            if not ays.lower().startswith('y'):
                logger.debug('  -- they say "%s". Aborting.', ays)
                print('Abort.')
                return

            for thing in things:
                try:
                    logger.info('Deleting %s...', thing)
                    thing.delete()
                    logger.info('  -- deleted.')
                except Exception as e:
                    logger.info('  -- failed: %s', e)
                    print('Failed to delete %s: %s' % (thing, e))

            print('Deleted.')
