import kepi.bowler_pub.settings
from django.core.management import get_commands, call_command
from django.core.management.base import CommandError
from django.conf import settings
from pkg_resources import resource_filename
import django
import os
import sys

KEPI_PREFIX = 'bowler_pub-'

def bowler_pub_commands():
    result = []
    for command in sorted(get_commands().keys()):
        if command.startswith(KEPI_PREFIX):
            result.append(command[len(KEPI_PREFIX):])

    return result

def setup():
    os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            "bowler_pub.settings"
            )
    django.setup()

def show_help():

    progname = os.path.basename(sys.argv[0])

    print()
    print('Syntax: %s <command-name>' % (progname,))
    print()
    print('  where <command-name> is one of')

    column = 0
    width = 70
    for command in bowler_pub_commands():

        if column+len(command)+1>width:
            print('')
            column = 0

        if column==0:
            print(' '*3, end='')
            column += 3

        print(' '+command, end='')
        column += len(command)+1
    
    print()
    print()
    print('For more information on any command, use')
    print('    %s <command-name> --help' % (progname,))
    print()

def main():
    setup()

    if len(sys.argv)<2 or sys.argv[1] in [
            'help', '--help', '-h',
            ]:
        show_help()
        return

    try:
        call_command(KEPI_PREFIX + sys.argv[1],
                *sys.argv[2:])
    except Exception as e:
        sys.stderr.write('%s\n' % (e,))
        sys.stderr.write('For a list of commands, run:\n')
        sys.stderr.write('    %s --help\n' % (sys.argv[0],))
