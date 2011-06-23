#!/usr/bin/python
#
# WSGI File for Django

# To use with apache2 server please read README file


import os, sys
my_location = os.path.abspath(os.path.split(__file__)[0])

# Insert Project path
PROJECT_PATH = os.path.join(my_location, '../')
sys.path.insert(0,PROJECT_PATH)

# Uncomment this if you use VirtualEnv
#
activate_this = PROJECT_PATH + "/../vtenv/bin/activate_this.py"
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(2, os.path.join(PROJECT_PATH, "apps"))
sys.stdout = sys.stderr

# Django

import django.core.handlers.wsgi
_application = django.core.handlers.wsgi.WSGIHandler()

def application(environ, start_response):
    """We need to hook application, to get DJANGO_MODE
    env variable
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    
    # Sets DJANGO_MODE if SetEnv xxx in apache2 vhost's
    if not os.environ.has_key('DJANGO_MODE'):
        if environ.has_key('DJANGO_MODE'):
            os.environ['DJANGO_MODE'] = environ['DJANGO_MODE']
        else:
            os.environ['DJANGO_MODE'] = 'production'

    return _application(environ, start_response)
