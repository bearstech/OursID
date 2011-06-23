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
#!/usr/bin/python
from openid.yadis.constants import YADIS_CONTENT_TYPE
from openid.message import Message
from openid.server.server import CheckIDRequest
from openid.yadis.services import applyFilter

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sessions.backends.db import SessionStore
from django.test.testcases import TestCase, TransactionTestCase
from django.http import HttpRequest
from django.contrib.sessions.middleware import SessionMiddleware

from account.models import RPHistory
from account.models import Identity
from server import util
from server import views
from account.models import TrustedConsumers
from urllib import quote_plus


def dummyRequest():
    request = HttpRequest()
    request.session = SessionStore('test')
    request.META['HTTP_HOST'] = 'example.invalid'
    request.META['REMOTE_ADDR'] = '127.0.0.30'
    request.META['SERVER_PROTOCOL'] = 'HTTP'
    request.user = User.objects.get(pk=1)
    return request

def dummyOidRequest(request, id, id_url, return_url = None):
    """Build an openid_request with id_url
    """
    # Set up the OpenID request we're responding to.
    op_endpoint = 'http://127.0.0.1:8080/endpoint'
    if return_url == None:
        return_url = 'http://127.0.0.1/%s' % (id,)
    message = Message.fromPostArgs({
        'openid.mode': 'checkid_setup',
        'openid.claimed_id': '',
        'openid.identity': id_url,
        'openid.return_to': return_url,
        'openid.sreg.required': 'postcode',
        })
    return CheckIDRequest.fromMessage(message, op_endpoint)

class TestProcessTrustResult(TransactionTestCase):
    """Note : Because of python-openid's Server() we need to store his state in
    sql, so we need TransactionTestCase in Django 1.1
    """
    fixtures = ['test/auser.yaml',]

    def generate_requests(self, id_url):
        self.request = dummyRequest()
        self.openid_request = dummyOidRequest(self.request, self.id(), id_url)
        self.zipcode = Identity.objects.filter(userprofile__user__pk=1)[0].zipcode
        util.setRequest(self.request, self.openid_request)

    def setUp(self):
        self.id_select = "http://specs.openid.net/auth/2.0/identifier_select"
        self.generate_requests(self.id_select)
        # some ids
        userid = "dummy"
        self.id_slash = util.getViewURL(self.request, 'ident', kwargs={'userid' : userid})
        self.id_noslash = self.id_slash.rstrip("/")

    def test_homepage(self):
        """Test homepage for any 500 error
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="%s"' % reverse('home'))

    def test_allow_default(self):
        """Test response without identity choice
        (server give the default identity)
        """
        self.request.POST['allow'] = 'Yes'
        userid = Identity.objects.filter(userprofile__user=self.request.user)[0].userid
        id_url = quote_plus(self.id_noslash)

        # Test without identity
        #
        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=id_res' in finalURL, finalURL)
        self.failUnless('openid.identity=%s' % id_url in finalURL, finalURL)
        self.failUnless('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        hist = RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=True)
        hist.delete()

    def test_allow(self):
        """Test with identity provided
        """
        self.request.POST['allow'] = 'Yes'

        # Test with identity
        #
        self.request.POST['identity'] = 'dummy'
        id_url = quote_plus(self.id_noslash)


        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=id_res' in finalURL, finalURL)
        self.failUnless('openid.identity=%s' % id_url in finalURL, finalURL)
        self.failUnless('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        hist = RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=True)

    def test_two_simultaneous_requests(self):
        oidrequest = dummyOidRequest(None, 13, 'http://specs.openid.net/auth/2.0/identifier_select', 'http://stackoverflow.com/users/authenticate/')
        response = self.client.get(oidrequest.encodeToURL('/server/endpoint/'))
        self.assertEqual(response.status_code, 302)
        logged = self.client.login(username='dummy', password='toto')
        self.assertTrue(logged, 'Login failed!')
        oidrequest = dummyOidRequest(None, 69, 'http://specs.openid.net/auth/2.0/identifier_select', 'http://64.34.119.12/users/authenticate/')
        response = self.client.get(oidrequest.encodeToURL('/server/endpoint/'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '64.34.119.12')

    def test_allowtrust(self):
        """Test with identity provided and retain trust
        """
        self.request.POST['alwaystrust'] = 'Yes'

        # Test with identity
        #
        self.request.POST['identity'] = 'dummy'
        id_url = quote_plus(self.id_noslash)

        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=id_res' in finalURL, finalURL)
        self.failUnless('openid.identity=%s' % id_url in finalURL, finalURL)
        self.failUnless('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        hist = RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=True)
        TrustedConsumers.objects.get(host=self.openid_request.trust_root, identity__userid='dummy', always=True)

    def test_cancel(self):
        """Test cancelation of auth
        """
        self.request.POST['cancel'] = 'Yes'
        self.request.POST['identity'] = 'dummy'

        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=cancel' in finalURL, finalURL)
        self.failIf('openid.identity=' in finalURL, finalURL)
        self.failIf('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=False)

    def test_stolen(self):
        """Test identity robt
        A user provide another user's identity, server must cancel auth.
        """
        self.request.POST['allow'] = 'Yes'

        # Test with identity
        #
        self.request.POST['identity'] = 'dummy2'

        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=cancel' in finalURL, finalURL)
        self.failIf('openid.identity=' in finalURL, finalURL)
        self.failIf('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=False)

    def test_deactivated(self):
        """Test identity deactivated
        A user provide his user's identity, but it is deactivated
        """
        self.request.POST['allow'] = 'Yes'

        # Test with identity
        #
        self.request.POST['identity'] = 'dommj'

        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=cancel' in finalURL, finalURL)
        self.failIf('openid.identity=' in finalURL, finalURL)
        self.failIf('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

    def test_allow_noslash(self):
        """Test with identity provided and non "/" ended
        """
        self.generate_requests(self.id_noslash)
        self.request.POST['allow'] = 'Yes'

        # Test with identity
        #
        self.request.POST['identity'] = 'dummy'
        id_url = quote_plus(self.id_noslash)
        from urllib import unquote_plus

        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=id_res' in finalURL, finalURL)
        self.failUnless('openid.identity=%s' % id_url in finalURL, finalURL)
        self.failUnless('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        hist = RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=True)

    def test_allow_slash(self):
        """Test with identity provided and "/" ended
        """
        self.generate_requests(self.id_slash)
        self.request.POST['allow'] = 'Yes'

        # Test with identity
        #
        self.request.POST['identity'] = 'dummy'
        id_url = quote_plus(self.id_slash)
        from urllib import unquote_plus

        response = views.processTrustResult(self.request)

        self.failUnlessEqual(response.status_code, 302)
        finalURL = response['location']
        self.failUnless('openid.mode=id_res' in finalURL, finalURL)
        self.failUnless('openid.identity=%s' % id_url in finalURL, finalURL)
        self.failUnless('openid.sreg.postcode=%s' % self.zipcode in finalURL, finalURL)

        # Test history entry
        hist = RPHistory.objects.get(host=self.openid_request.trust_root, auth_result=True)

class TestShowDecidePage(TestCase):
    fixtures = ['test/auser.yaml',]
    def test_unreachableRealm(self):
        self.request = dummyRequest()

        id_url = util.getViewURL(self.request, "home")

        # Set up the OpenID request we're responding to.
        op_endpoint = 'http://127.0.0.1:8080/endpoint'
        message = Message.fromPostArgs({
            'openid.mode': 'checkid_setup',
            'openid.identity': id_url,
            'openid.return_to': 'http://unreachable.invalid/%s' % (self.id(),),
            'openid.sreg.required': 'postcode',
            })
        self.openid_request = CheckIDRequest.fromMessage(message, op_endpoint)

        util.setRequest(self.request, self.openid_request)

        response = views.showDecidePage(self.request, self.openid_request)
        self.failUnless('trust_root_valid is Unreachable' in response.content,
                        response)

class TestGenericXRDS(TestCase):
    fixtures = ['test/auser.yaml',]
    def test_genericRender(self):
        """Render an XRDS document with a single type URI and a single endpoint URL
        Parse it to see that it matches."""
        request = dummyRequest()

        type_uris = ['A_TYPE']
        endpoint_url = 'A_URL'
        response = util.renderXRDS(request, type_uris, [endpoint_url])
        requested_url = 'http://requested.invalid/'
        (endpoint,) = applyFilter(requested_url, response.content)

        self.failUnlessEqual(YADIS_CONTENT_TYPE, response['Content-Type'])
        self.failUnlessEqual(type_uris, endpoint.type_uris)
        self.failUnlessEqual(endpoint_url, endpoint.uri)
