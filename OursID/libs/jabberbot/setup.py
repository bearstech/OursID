#!/usr/bin/env python
# Setup script for python-jabberbot
# by Frederic

from setuptools import setup

import os

readme = open(os.path.join(os.path.dirname(__file__), 'README')).read()

VERSION = "0.13"

setup(
        name     = 'jabberbot',
        version  = VERSION,
        install_requires = [
		'xmpppy',
		],

        description  = 'A simple framework for creating Jabber/XMPP bots and services in Python',
        long_description = readme,
        author       = 'Thomas Perl',
        author_email = 'm@thp.io',
        url          = 'http://thp.io/2007/python-jabberbot/',
        download_url = 'http://thp.io/2007/python-jabberbot/jabberbot-%s.tar.gz' % VERSION,
        license      = 'GPL or later',
        keywords     = 'jabber bot xmpp',
        classifiers  = [
                    'Development Status :: 4 - Beta Development Status',
                    'Intended Audience :: Developers',
                    'Programming Language :: Python',
                    'Topic :: Software Development :: Libraries :: Python  Modules',
                ],
        py_modules   = (
                'jabberbot',
        ),
)

