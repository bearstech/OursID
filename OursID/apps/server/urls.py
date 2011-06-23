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

urlpatterns = patterns('server.views',
    url(r'^$', 'server', name='server'),
    url(r'^xrds$', 'idpXrds', name='idpXrds'),
    url(r'^processTrustResult/$', 'processTrustResult', name='prslt'),
#    url(r'^user/$', 'idPage', name='idpage'),
    url(r'^endpoint/$', 'endpoint', name="endpoint"),
    url(r'^oidrequest/(?P<oidrequest_id>\d*)/*(?P<action>[\w]*)$', 'oidrequest', name='oidrequest'),
    url(r'^oidRequestStatus$', 'oidRequestStatus', name='oidRequestStatus'),
    url(r'^processRemoteTrustResult$', 'processRemoteTrustResult', name='processRemoteTrustResult'),
    url(r'^registerC2DM/(?P<registration_id>[\w_-]+)$', 'registerC2DM', name='registerC2DM'),
    #url(r'^trust/$', 'trustPage', name='trustpage'),
)
