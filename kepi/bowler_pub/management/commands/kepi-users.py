from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.create import create
from kepi.bowler_pub.management import KepiCommand
import os
import logging

logger = logging.Logger('kepi')

class Command(KepiCommand):

    help = 'list, show, or edit users'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('--create',
                help='create a new user',
                metavar='USERNAME',
                )

    def handle(self, *args, **options):

        super().handle(*args, **options)

        if options['create'] is not None:
            self._create(*args, **options)
        else:
            self._list(*args, **options)

    def _list(self, *args, **options):
        results = AcActor.objects.filter_local_only()

        if not results.exists():
            self.stdout.write(
                    self.style.ERROR(
                        "No users found. To create a user, use "+\
                                "'bowler_pub users --create fred'."
                        ))
            return

        for obj in results:
            self.stdout.write('%s' % (obj.id,))

    def _create(self, *args, **options):

        new_name = options['create']

        self.stdout.write('Creating user %s' % (
            new_name,))

        spec = {
            'type': 'Person',
            'id': '@'+new_name,
                }

        logger.debug('Creating object with spec %s',
                spec)

        result = create(
                value=spec,
                is_local_user = True,
                run_side_effects = True,
                run_delivery = False,
                )

        logger.info('Created object: %s',
                result)

        if result is None:
            self.stdout.write(self.style.WARNING(
                'No object was created. (Try --debug-mode to discover why.)',
                ))
        else:
            self.stdout.write('Created: %s' % (result,))

