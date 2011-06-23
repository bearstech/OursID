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
# Django settings for oursid project.
# Bearstech flavored
import os, sys

# Get absolute project's path
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])

# Theses settings are different with env variables
#
# We wait a DJANGO_MODE environment variable with values :
# 'production' OR 'development'
#
DJANGO_MODE = os.environ.get('DJANGO_MODE', False)
PRODUCTION_MODE = ( DJANGO_MODE == 'production' )
DEVELOPMENT_MODE = ( DJANGO_MODE == 'development' )
LOCAL_MODE = not ( PRODUCTION_MODE or DEVELOPMENT_MODE )



#################################
# Hosting configuration section #
#################################

ADMINS = (
#     ('Admin', 'youremail@mail.com'),
)

SERVER_EMAIL = "server@mail.com"
DEFAULT_FROM_EMAIL = "noreply@mail.com"

# Some parameters can change between dev mode and prod mode
if PRODUCTION_MODE :
    DEBUG = False
    CACHE_BACKEND = 'memcached://127.0.0.1:11211/'
else :
    # DEVELOPMENT and LOCAL
    DEBUG = True
    CACHE_BACKEND = "locmem:///"

DATABASES = {'default' : {}}

if not LOCAL_MODE:
    # DEVELOPMENT and PRODUCTION
    DATABASES["default"]["ENGINE"] = 'mysql'  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
    DATABASES["default"]["NAME"] = 'openid'
    DATABASES["default"]["OPTIONS"] = {
        'read_default_file': '~/.my.cnf',
        }
else :
    # In local mode use localdb
    DATABASES["default"]["ENGINE"] = 'django.db.backends.sqlite3'  # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
    DATABASES["default"]["NAME"] = os.path.join(PROJECT_PATH, 'db.dat')

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
# We append PROJECT_PATH's absolute path
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

###############################################################################
# Dev section

TEMPLATE_DEBUG = DEBUG

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
LOGIN_URL = '/account/login'

AUTHENTICATION_BACKENDS = (
    'account.email-auth.EmailBackend',
 )

AUTH_PROFILE_MODULE = 'account.userprofile'

# Make this unique, and don't share it with anybody.
SECRET_KEY = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "account.context_processors.loginform",
    "django.core.context_processors.request",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'account',
    'server',
    'cms',
    'mptt',
    'photologue',
    'c2dm_notifier',
    'oauth_forwarder',
)

# Insert Here your Recaptcha Public and Private keys
RECAPTCHA_PUBLIC = ""
RECAPTCHA_PRIVATE = ""

INTERNAL_IPS = ("127.0.0.1",)

C2DM_AUTH_TOKEN = ''

JABBER_ID = 'setme@correct.jid'
JABBER_PWD = 'setmetoo'
