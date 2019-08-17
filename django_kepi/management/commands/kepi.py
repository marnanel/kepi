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

    def _handle_post(self, *args, **options):
        self.stdout.write('Note\n')

        note = create(value={
            'type': 'Note',
            'attributedTo': self._actor,
            'to': self._actor['followers'],
            'cc': 'https://www.w3.org/ns/activitystreams#Public',
            'content': options['text'],
            },
            is_local_user=True,
            )
        logger.info('Note created: %s', note)

        creation = create(value={
            'type': 'Create',
            'actor': self._actor,
            'object': note,
            'to': self._actor['followers'],
            'cc': 'https://www.w3.org/ns/activitystreams#Public',
            },
            is_local_user=True,
            run_side_effects=False,
            run_delivery=True,
            )
        logger.info('Create created: %s', creation)

    def _handle_posts(self, *args, **options):
        results = Item.objects.filter(
                f_attributedTo = self._actor.id,
                )

        if not results.exists():
            self.stdout.write(
                    self.style.ERROR(
                        "No posts found."
                        ))
            return

        for obj in results:
            self.stdout.write(' - %s' % (obj,))

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

        parser_post = subparsers.add_parser('post')
        parser_post.set_defaults(func=self._handle_post)
        parser_post.add_argument('text',
                help='what to post. (Enclose in quotes if it contains spaces.)',
                )

        parser_posts = subparsers.add_parser('posts')
        parser_posts.set_defaults(func=self._handle_posts)

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
