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
from account.forms import SubscribeWizard, UsernameForm, SubscribeForm, CaptchaForm


urlpatterns = patterns('account.views',
   url(r'^create$', SubscribeWizard([SubscribeForm, CaptchaForm ,UsernameForm]), name='accountcreate'),
   url(r'^create/ok$', 'create', name='accountcreateok'),
   url(r'^login$', 'login_form', name='login'),
   url(r'^login_json$', 'login_json', name='login_json'),
   url(r'^logout$', 'logout_form', name='logout'),
   url(r'^identities/$', 'ident_list', name='identlist'),
   url(r'^identities/change$', 'ident_change', name='identchange'),
   url(r'^identities/(?P<userid>[\w\-]+)$', 'ident_show', name='identshow'),
   url(r'^identities/(?P<userid>[\w\-]+)/modify$', 'ident_edit', name='identedit'),
   url(r'^identities/(?P<userid>[\w\-]+)/new$', 'ident_create', name='identcreate'),
   url(r'^identities/(?P<userid>[\w\-]+)/delete$', 'ident_delete', name='identdelete'),
   url(r'^identities/(?P<userid>[\w\-]+)/revoke_assoc$', 'ident_revokeassoc', name='identrevokeassoc'),
   url(r'^$', 'details', name='accountdetail'),
   url(r'^delete$', 'delete', name='accountdelete'),
   url(r'^edit$', 'edit', name='accountedit'),
   url(r'^edit/password$', 'editpasw', name='accounteditpasw'),
   url(r'^edit/password/ok$', 'editpaswok', name='accounteditpaswok'),
   url(r'^edit/email$', 'editemail', name='accounteditemail'),
   url(r'^edit/email/ok$', 'editemailok', name='accounteditemailok'),
   url(r'^edit/notification$', 'editnotif', name='accounteditnotif'),
   url(r'^edit/notification/ok$', 'editnotifok', name='accounteditnotifok'),
   url(r'^edit/oauth$', 'editoauth', name='accounteditoauth'),
   url(r'^edit/oauth/ok$', 'editoauthok', name='accounteditoauthok'),
   url(r'^history$', 'history', name='accounthistory'),
   url(r'^history/(?P<page>\d+)$', 'history', name='accounthistorypage'),
   url(r'^confirm/(?P<code>[\w\-]+)$', 'confirm', name='confirm'),
   )

urlpatterns += patterns('django.contrib.auth.views',
    url(r'^lostpwd/$', 'password_reset', {'template_name':'account/passreset/password_reset_form.html', 'email_template_name':'account/passreset/password_reset_email.txt'}, name='resetform'),
    url(r'^lostpwd/done/$', 'password_reset_done', {'template_name':'account/passreset/password_reset_done.html'}),
    url(r'^lostpwd/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm', {'template_name':'account/passreset/password_reset_confirm.html'}, name='pwdreset'),
    url(r'^lostpwd/complete/$', 'password_reset_complete', {'template_name':'account/passreset/password_reset_complete.html'}),
)

