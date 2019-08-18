from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_kepi.models import *
from django_kepi.create import create
from django_kepi.management import KepiCommand
import os
import logging

logger = logging.Logger('django_kepi')

class Command(KepiCommand):

    help = 'post a status'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('text',
                help='what to post. (Enclose in quotes if it contains spaces.)',
                )

    def handle(self, *args, **options):

        super().handle(*args, **options)

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


