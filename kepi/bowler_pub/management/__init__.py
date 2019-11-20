from django.core.management.base import BaseCommand, CommandError
from kepi.bowler_pub.models import *
from django.conf import settings
import logging
import os
import re

ENVIRON_USER = 'KEPI_USER'

logger = logging.Logger('kepi')

class KepiCommand(BaseCommand):

    def _get_actor_name(self):
        if self._actor is None:
            self.stdout.write(self.style.ERROR(
                "Which user are you? Use --actor, or set %s." % (
                    ENVIRON_USER,
                    )))
            raise ValueError('actor not specified')
        else:
            return self._actor

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
            if ENVIRON_USER in os.environ:
                self._actor = os.environ[ENVIRON_USER]
            else:
                # possibly also:
                #    - if there's only one user, use that
                #    - if there's a user with the same name as
                #       the current Unix user, use that
                self._actor = None
        else:
            try:
                self._actor = AcActor.objects.get(
                        id = '@'+options['actor'],
                        )
            except AcActor.DoesNotExist:
                self._actor = None

def objects_by_keywords(keywords):
    """
    Finds a set of kepi objects specified by their ids.
    """

    result = []

    for keyword in keywords:
        try:
            result.append(AcObject.objects.get(
                    id = keyword,
                    ))
        except AcObject.DoesNotExist:
            raise KeyError(
                'I can\'t find %s.' % (keyword,)
                )

    return result
