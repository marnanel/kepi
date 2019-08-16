from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_kepi.models import *
from django_kepi.create import create
import os
import logging

logger = logging.Logger('django_kepi')

ENVIRON_USER = 'KEPI_USER'

class Command(BaseCommand):

    help = 'control kepi'

    def _handle_follow(self, *args, **options):
        self.stdout.write('Follow\n')

        obj = create(value={
            'type': 'Follow',
            'actor': self._actor,
            'to': options['whom'],
            'object': options['whom'],
            },
            is_local_user=True,
            )
        logger.info('Follow created: %s', obj)

    def add_arguments(self, parser):

        parser.add_argument('--actor', '-a',
                type=str,
                default=None)
        parser.add_argument('--debug-mode', '-d',
                help='run in debug mode (with logging)',
                action='store_true',
                default=None)
        subparsers = parser.add_subparsers(help='commands')

        parser_follow = subparsers.add_parser('follow')
        parser_follow.set_defaults(func=self._handle_follow)
        parser_follow.add_argument('whom',
                help='account to follow',
                )

    def _find_source_username(self):
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

    def handle(self, *args, **options):

        if options['debug_mode']:
            settings.DEBUG = True

        if options['actor'] is None:
            options['actor'] = self._find_source_username()
            if options['actor'] is None:
                return

        try:
            self._actor = Actor.objects.get(
                    remote_url = None,
                    active = True,
                    f_preferredUsername = options['actor'],
                    )
        except Actor.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                "%s is not a known user." % (options['actor'],)))
            return

        options['func'](*args, **options)
