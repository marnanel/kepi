import kepi.settings
from django.core.management import get_commands, call_command
from django.conf import settings
from pkg_resources import resource_filename
import django
import os

KEPI_PREFIX = 'kepi-'

def show_commands():
    for command in sorted(get_commands().keys()):
        if command.startswith(KEPI_PREFIX):
            print(command[len(KEPI_PREFIX):])

def main():

    #resource_filename('kepi', 'settings.py'),
    #
    os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            "kepi.settings"
            )

    django.setup()

    show_commands()

    call_command('kepi-list')
