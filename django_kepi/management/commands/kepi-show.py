from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_kepi.models import *
from django_kepi.create import create
from django_kepi.management import KepiCommand
import os
import re
import logging
import json

logger = logging.Logger('django_kepi')

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

        statuses = AcItem.objects.filter(
                remote_url = None,
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
            self._show_thing(thing, *args, **options)

    ################################

    def _show_by_number(self, number, *args, **options):
        try:
            something = AcObject.objects.get(
                    # we don't require remote_url to be None
                    # if they're giving us an exact number
                    number = number,
                    )

        except AcObject.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                'There is nothing with the number %s.' % (number,)
                ))
            return

        self._show_thing(something,
                *args, **options)

        return

    def _show_by_keyword(self, name, *args, **options):

        name = name.lower()

        username_match = re.match(r'@([a-z0-9_-]+)$', name)

        if username_match:
            try:
                somebody = AcActor.objects.get(
                        remote_url = None,
                        f_preferredUsername = username_match.group(1),
                        )

                self._show_thing(somebody,
                        *args, **options)

                return

            except AcActor.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    'There is no user named %s.' % (name,)
                    ))
                return

        eight_digits_match = re.match('[0-9a-f]{8}$', name)
        if eight_digits_match:
            self._show_by_number(eight_digits_match.group(0),
                    *args, **options)
            return

        bracketed_eight_digits_match = re.match('\(([0-9a-f]{8})\)$',
                name)
        if bracketed_eight_digits_match:
            self._show_by_number(bracketed_eight_digits_match.group(1),
                    *args, **options)
            return

        self.stdout.write(self.style.WARNING(
            'I don\'t know what %s means.' % (name,)
            ))

    def handle(self, *args, **options):

        super().handle(*args, **options)

        for thing in options['id']:
            logger.debug('Showing: %s', thing)
            self._show_by_keyword(thing, *args, **options)
