from django.core.management.base import BaseCommand, CommandError
import django_kepi.models

class Command(BaseCommand):
    help = 'create a kepi object'

    def add_arguments(self, parser):
        parser.add_argument('type', type=str,
                help="the type of object (e.g. 'Person')")
        parser.add_argument(
                'fields', metavar='FIELD=VALUE', nargs='*', type=str,
                help='fields for the new object')

    def handle(self, *args, **options):

        fields = {
                'type': options['type'].title(),
                }

        for fv in options['fields']:
            try:
                f, v = fv.split('=', maxsplit=1)
            except ValueError:
                self.stderr.write(self.style.ERROR(
                    fv + ' needs to be in the format FIELD=VALUE',
                    ))
                continue

            fields[f.lower()] = v

        created = None

        print(fields)

        try:
            created = django_kepi.models.create(**fields)
            self.stdout.write(self.style.SUCCESS('Created object.'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(e.args[0]))

        if created:
            self.stdout.write(self.style.NOTICE(created.pretty))
