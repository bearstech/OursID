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

urlpatterns = patterns('cms.views',
    url(r'^(?P<lang>[\w]{2})/(?P<url>[\w\-\/]+)/p(?P<page>[\d]+)$', 'page', name='cmsblogpage'),
    #url(r'^(?P<slug>[\w\-\/]+)/$', 'folder', name='cmsfolder'),
    url(r'^(?P<lang>[\w]{2})/(?P<url>[\w\-\/]+)$', 'page', name='cmspage'),
    url(r'^(?P<lang>[\w]{2})/$', 'rootpage', name='cmsroot'),
    url(r'^(?P<url>[\w\-\/]+)$', 'nolang', name='nolang'),
)

urlpatterns += patterns('django.views.generic.simple',
    url(r'^$', 'redirect_to', {'url': 'faq'}),
)
