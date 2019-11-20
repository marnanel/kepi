from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.create import create
from kepi.bowler_pub.management import KepiCommand, objects_by_keywords
import os
import logging
import json

logger = logging.Logger('kepi')

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

    ################################

    def handle(self, *args, **options):

        super().handle(*args, **options)

        try:
            things = objects_by_keywords(options['id'])
            logger.info('Requesting deletion of %s, which give %s',
                    options['id'], things)
        except KeyError as ke:
            self.stdout.write(self.style.ERROR(
                ke.args[0],))
            logger.info('Requesting deletion of %s failed: %s',
                    options['id'], ke.args[0])
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
