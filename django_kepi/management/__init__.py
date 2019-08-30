from django.core.management.base import BaseCommand, CommandError
from django_kepi.models import *
from django.conf import settings
import logging
import os

ENVIRON_USER = 'KEPI_USER'

logger = logging.Logger('django_kepi')

class KepiCommand(BaseCommand):

    def _actor_name(self):
        if ENVIRON_USER in os.environ:
            return os.environ[ENVIRON_USER]

        # possibly also:
        #    - if there's only one user, use that
        #    - if there's a user with the same name as
        #       the current Unix user, use that

        self.stdout.write(self.style.ERROR(
            "Which user are you? Use --actor, or set %s." % (
                ENVIRON_USER,
                )))
        return None

    def add_arguments(self, parser):
        parser.add_argument('--actor', '-a',
                help='actor to act as',
                type=str,
                default=None)
        parser.add_argument('--debug-mode', '-d',
                help='run in debug mode (with logging)',
                action='store_true',
                default=None)

    def handle(self, *args, **options):

        # Written out like this so it's easier to add things
        if options['debug_mode']:
            settings.DEBUG = True
        else:
            settings.DEBUG = False

        if options['actor'] is None:
            options['actor'] = self._actor_name()
            if options['actor'] is None:
                return

        try:
            self._actor = AcActor.objects.get(
                    remote_url = None,
                    active = True,
                    f_preferredUsername = options['actor'],
                    )
        except AcActor.DoesNotExist:
            self._actor = None
