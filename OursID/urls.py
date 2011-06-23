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
from django.conf.urls.defaults import *

import settings
from os import path as os_path

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #url(r'^$', 'django.views.generic.simple.redirect_to', {'url' : 'home'}),
    (r'^account/', include('account.urls')),
    (r'^server/', include('server.urls')),
    url(r'^site/', include('cms.urls')),

    (r'^oidadmin/', include(admin.site.urls)),
    (r'^oidadmin/doc/', include('django.contrib.admindocs.urls')),

    (r'^photologue/', include('photologue.urls')),
    url(r'^oauth/', include('oauth_forwarder.urls', namespace='oauth_forwarder')),

    url(r'^(?P<userid>[\w\-]+)$', 'account.views.ident_show', name='ident', kwargs={'direct':True}),
    url(r'^(?P<userid>[\w\-]+)/$', 'account.views.ident_show', name='ident', kwargs={'direct':True}),
    url(r'^$', 'account.views.idPage', name='home'),

)


if settings.LOCAL_MODE:
    urlpatterns += patterns('',

    # if we are in local mode we need django to serve medias
     (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os_path.join(settings.PROJECT_PATH, 'media')}),

    )

