#!/usr/bin/env python

# this is a manage.py for reusable libraries
# it is dedicated to the public domain
# feel free to copy it into your project

import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_settings")
    execute_from_command_line(sys.argv)
