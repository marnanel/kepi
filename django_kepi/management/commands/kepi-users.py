from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_kepi.models import *
from django_kepi.create import create
from django_kepi.management import KepiCommand
import os
import logging

logger = logging.Logger('django_kepi')

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
        results = AcActor.objects.filter(
                remote_url = None,
                )

        if not results.exists():
            self.stdout.write(
                    self.style.ERROR(
                        "No users found. To create a user, use "+\
                                "'kepi users --create fred'."
                        ))
            return

        for obj in results:
            self.stdout.write('%s' % (obj.f_preferredUsername,))

    def _create(self, *args, **options):

        new_name = options['create']

        self.stdout.write('Creating user %s' % (
            new_name,))

        spec = {
            'type': 'Person',
            'preferredUsername': new_name,
                }

        logger.debug('Creating object with spec %s',
                spec)

        result = create(
                value=spec,
                is_local_user = True,
                run_side_effects = True,
                run_delivery = False,
                using_commandline_names = True,
                )

        logger.info('Created object: %s',
                result)

        if result is None:
            self.stdout.write(self.style.WARNING(
                'No object was created. (Try --debug-mode to discover why.)',
                ))
        else:
            self.stdout.write('Created: %s' % (result,))

