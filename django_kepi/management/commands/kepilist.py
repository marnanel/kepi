from django.core.management.base import BaseCommand, CommandError
import django_kepi.models

class Command(BaseCommand):
    help = 'list kepi objects'

    def add_arguments(self, parser):
        parser.add_argument('filters', nargs='*',
                metavar='FIELD=VALUE', type=str,
                help='field=value pairs, or IDs, to filter on')

    def handle(self, *args, **options):

        filters = []
        for fv in options['filters']:
            if '=' in fv:
                f, v = fv.split('=', maxsplit=1)
                filters.append( (f,v) )
            else:
                filters.append( ('number', fv) )

        # This can certainly be optimised a lot

        count = 0
        for thing in django_kepi.models.Object.objects.all():

            usable = True
            for f,v in filters:
                if thing[f]!=v:
                    break
            else:
                self.stdout.write(thing.pretty)
                count += 1

        if count==0:
            self.stdout.write(self.style.ERROR('Nothing found'))
