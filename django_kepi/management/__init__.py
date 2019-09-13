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
            self._actor = AcActor.objects.get_local_only(
                    f_preferredUsername = options['actor'],
                    )
        except AcActor.DoesNotExist:
            self._actor = None

def objects_by_keywords(keywords):
    """
    Finds a set of kepi objects specified by a series of keywords.

    "keywords" is a list of strings.
    Returns a list of objects on success.

    An ID number consists of eight hex digits.

    If any of the strings in "keywords" contain one or more
    bracketed ID numbers, this function returns a list of the
    objects those numbers represent, in order.
    In this case, no other representation of an object will be considered.
    It doesn't matter if some of the lines don't contain any
    bracketed numbers at all.
    If any of the numbers don't correspond to a current object,
    raises KeyError.

    Otherwise, each string in "keywords" must represent either:
      - an ID number, as above
      - a username preceded by @
    If any string doesn't represent either, raise KeyError.
    Otherwise, we return a list of the objects referred to,
    in the same order.
    """

    def object_by_number(number):
        try:
            result = AcObject.objects.get(
                    id = '/'+number,
                    )

        except AcObject.DoesNotExist:
            raise KeyError(
                'There is nothing with the number %s.' % (number,)
                )

        return result

    bracketed_eight_digits_match = re.findall(r'\(([0-9a-f]{8})\)',
            ' '.join(keywords),
            re.IGNORECASE,
            )
    if bracketed_eight_digits_match:
        return [object_by_number(n) for n in bracketed_eight_digits_match]

    result = []
    for keyword in keywords:
        username_match = re.match(r'@([a-z0-9_-]+)$', keyword,
                re.IGNORECASE)

        if username_match:
            try:
                somebody = AcActor.objects.get_local_only(
                        f_preferredUsername = username_match.group(1),
                        )

                result.append(somebody)
                continue

            except AcActor.DoesNotExist:
                raise KeyError(
                    'There is no user named %s.' % (keyword,)
                    )

        eight_digits_match = re.match(r'([0-9a-f]{8})$', keyword)
        if eight_digits_match:
            result.append(object_by_number(eight_digits_match.group(1)))
            continue

        raise KeyError(
            'I don\'t know what %s means.' % (keyword,)
            )

    return result
