from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django_kepi.models import *
from django_kepi.create import create
from django_kepi.management import KepiCommand
import os
import logging

logger = logging.Logger('django_kepi')

class Command(KepiCommand):

    help = 'list objects'

    def handle(self, *args, **options):

        super().handle(*args, **options)

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


