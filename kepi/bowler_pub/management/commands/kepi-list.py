from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from kepi.bowler_pub.models import *
from kepi.bowler_pub.create import create
from kepi.bowler_pub.management import KepiCommand
import os
import logging

logger = logging.Logger('kepi')

class Command(KepiCommand):

    help = 'list objects'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('--all',
                help='show cached remote objects as well',
                action='store_true',
                )

    def handle(self, *args, **options):

        super().handle(*args, **options)

        if options['all']:
            results = AcObject.objects.all()
        else:
            results = AcObject.objects.filter_local_only()

        if not results.exists():
            self.stdout.write(
                    self.style.ERROR(
                        "Nothing found."
                        ))
            return

        for obj in results:
            self.stdout.write(' - %s' % (obj,))


