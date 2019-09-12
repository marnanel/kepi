from django.core.management.base import BaseCommand, CommandError
from django_kepi.models import *
from django.conf import settings
import logging
import os
import re

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

def object_by_keyword(keyword):

    def object_by_number(number):
        try:
            result = AcObject.objects.get(
                    # we don't require remote_url to be None
                    # if they're giving us an exact number
                    number = number,
                    )

        except AcObject.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                'There is nothing with the number %s.' % (number,)
                ))
            return None

        return result

    keyword = keyword.lower()

    username_match = re.match(r'@([a-z0-9_-]+)$', keyword)

    if username_match:
        try:
            somebody = AcActor.objects.get(
                    remote_url = None,
                    f_preferredUsername = username_match.group(1),
                    )

            return somebody

        except AcActor.DoesNotExist:
            self.stdout.write(self.style.WARNING(
                'There is no user keywordd %s.' % (keyword,)
                ))
            return None

    eight_digits_match = re.match('([0-9a-f]{8})$', keyword)
    if eight_digits_match:
        return object_by_number(eight_digits_match.group(1))

    bracketed_eight_digits_match = re.match('\(([0-9a-f]{8})\)',
            keyword)
    if bracketed_eight_digits_match:
        return object_by_number(bracketed_eight_digits_match.group(1))

    self.stdout.write(self.style.WARNING(
        'I don\'t know what %s means.' % (keyword,)
        ))
    return None
