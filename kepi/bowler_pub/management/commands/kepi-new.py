from kepi.bowler_pub.create import create
from kepi.bowler_pub.management import KepiCommand
import logging

logger = logging.Logger('kepi')

class Command(KepiCommand):

    help = 'create an object'

    def add_arguments(self, parser):

        super().add_arguments(parser)

        parser.add_argument('spec',
                help='fields of new object',
                nargs='+',
                metavar='FIELD=VALUE',
                )

        parser.add_argument('--no-side-effects',
                help='don\'t run side effects on activities',
                action='store_true',
                )

        parser.add_argument('--no-delivery',
                help='don\'t attempt to deliver the new object',
                action='store_true',
                )

    def handle(self, *args, **options):

        super().handle(*args, **options)

        spec = {}

        for arg in options['spec']:
            if '=' not in arg:
                self.stdout.write(self.style.ERROR(
                    'options to "create" must be in the form '+\
                            '"field=value": %s' % (
                                arg,
                                )))
                return

            field, value = arg.split('=', 1)

            spec[field] = value

        logger.debug('Creating object with spec %s',
                spec)

        result = create(
                value=spec,
                is_local_user = True,
                run_side_effects = not options['no_side_effects'],
                run_delivery = not options['no_delivery'],
                )

        logger.info('Created object: %s',
                result)

        if result is None:
            self.stdout.write(self.style.WARNING(
                'No object was created. (Try --debug-mode to discover why.)',
                ))
        else:
            self.stdout.write('Created: %s' % (result,))

