from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.create import create
from kepi.bowler_pub.management import KepiCommand
import os
import logging

logger = logging.Logger('kepi')

class Command(KepiCommand):

    help = 'post a status'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('text',
                help='what to post. (Enclose in quotes if it contains spaces.)',
                )

    def handle(self, *args, **options):

        super().handle(*args, **options)

        actor = self._actor
        if actor is None:
            self.stdout.write(self.style.ERROR(
                'You need to specify an actor, using --actor <username>.',
                ))
            return

        note = create(value={
            'type': 'Note',
            'attributedTo': actor,
            'to': 'https://www.w3.org/ns/activitystreams#Public',
            'cc': actor['followers'],
            'content': options['text'],
            },
            is_local_user=True,
            )
        logger.info('Note created: %s', note)

        if note is None:
            self.stdout.write(self.style.WARNING(
                'No note was created. (Try --debug-mode to discover why.)',
                ))
            return

        creation = create(value={
            'type': 'Create',
            'actor': actor,
            'object': note,
            'to': 'https://www.w3.org/ns/activitystreams#Public',
            'cc': actor['followers'],
            },
            is_local_user=True,
            run_side_effects=False,
            run_delivery=True,
            )
        logger.info('Create created: %s', creation)

        if creation is None:
            self.stdout.write(self.style.WARNING(
                'No creation activity was created. (Try --debug-mode to discover why.)',
                ))
            return

        self.stdout.write('Created: %s' % (note,))
