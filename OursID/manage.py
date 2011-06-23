#!/usr/bin/env python
"""
    Oursid - A django openid provider
    Copyright (C) 2009  Bearstech

    This file is part of Oursid - A django openid provider

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys

import os
from os.path import abspath, dirname, join

# Insert Pinax paths
PROJECT_ROOT = abspath(dirname(__file__))

# Uncomment this if you use Virtualenv
#
activate_this = PROJECT_ROOT + "/../vtenv/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))

# Adds directories apps and libs into PYTHON_PATH
sys.path.insert(0, join(PROJECT_ROOT, "libs"))
sys.path.insert(0, join(PROJECT_ROOT, "apps"))

# Normal django...

if not os.environ.has_key('DJANGO_MODE'): 
    os.environ['DJANGO_MODE'] = 'local'
    print "------------------------------------------------------------------------------"
    print " Manage in LOCAL mode : set DJANGO_MODE env variable for prod and dev servers."
    print " See README for more informations"
    print "------------------------------------------------------------------------------"
    from time import sleep
    sleep(1)

from django.core.management import execute_manager

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)
