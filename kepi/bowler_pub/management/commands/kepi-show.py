from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.create import create
from kepi.bowler_pub.management import KepiCommand, objects_by_keywords
from collections import abc
import os
import logging

logger = logging.Logger('kepi')

class Command(KepiCommand):

    help = 'show users, statuses, and so on'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('id',
                help='the object to show: @name for a user, or an '+\
                        '8-digit number',
                metavar='OBJECT',
                nargs='+',
                )

        parser.add_argument('--raw',
                help='print the actual fields; don\'t try to interpret them',
                action='store_true',
                )

        parser.add_argument('--json',
                help='pretty-print the json that would be sent over the wire',
                action='store_true',
                )

    ################################

    def _show_actor(self, somebody, *args, **options):

        followers = Following.objects.filter(
                following = somebody,
                )
        following = Following.objects.filter(
                follower = somebody,
                )
        statuses = [x['object__obj'] for x in
                AcCreate.objects.filter(
                f_actor = somebody.short_id,
                )]

        result = [
                ('url', somebody.url),
                ('bio', somebody.f_summary),
                ('auto-follow', somebody.auto_follow),
                ('followers', followers),
                ('following', following),
                ('statuses', statuses),
                ]

        self._display_table(result,
                title=somebody.id,
                )

    def _show_activity(self, activity, *args, **options):

        result = [
        ('type', activity.f_type),
        ('actor', activity['actor']),
        ('object', activity['object']),
        ('target', activity['target']),
        ]

        self._display_table(result,
                title='activity %s' % (activity.number,),
                )

    def _show_item(self, item, *args, **options):

        # XXX date etc
        # XXX find activity which created it

        result = [
                ('by', item['attributedTo']),
                ('date', item['published']),
                ('content', item['content']),
                ('visibility', item.visibility),
                ]

        if item.is_reply:
            result.append(('reply_to', item['replyTo']))

        self._display_table(result,
                title='item %s' % (item.number,),
                )

    def _display_table(self, items,
            title=None):

        if title:
            print('== %s ==' % (title,))

        width = max([len(f) for f,v in items])

        for f,v in items:
            print('%*s: ' % (
                width,
                f,
                ),
                end='')

            if isinstance(v, str):
                print(v)
            elif isinstance(v, abc.Iterable):

                print(len(v))

                spaces = (' '*width)+'    '

                for line in v:
                    print(spaces+str(line))
            else:
                print(v)

    def _show_raw_object(self, thing, *args, **options):
        self._display_table(
            sorted(thing.activity_form.items()))

    def _show_json(self, thing, *args, **options):

        from kepi.bowler_pub.utils import as_json

        print(as_json(thing.activity_form))

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

        logger.debug('Showing: %s', options['id'])

        try:
            things = objects_by_keywords(options['id'])
            logger.debug('  -- which are: %s', things)

            for thing in things:
                self._show_thing(thing, *args, **options)
        except KeyError as ke:
            logger.debug('  -- which don\'t all exist: %s',
                    ke.args[0])
            self.stdout.write(self.style.WARNING(
                ke.args[0],))

