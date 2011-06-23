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
"""

TODO : relative URLs in tests

"""


from django.test import TestCase

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from account.forms import SubscribeForm, DeleteForm, LoginForm, UsernameForm, SubscribeWizard, CaptchaForm
from models import Identity, IdentityPerms, UserProfile, TrustedConsumers
from django.http import HttpRequest
from django.contrib.sessions.backends.db import SessionStore

from django.utils.translation import ugettext_lazy as _

from django.core.urlresolvers import reverse
from django.core import mail

def dummyRequest():
    request = HttpRequest()
    request.session = SessionStore('test')
    request.META['HTTP_HOST'] = 'example.invalid'
    request.META['REMOTE_ADDR'] = '127.0.0.30'
    request.META['SERVER_PROTOCOL'] = 'HTTPS'
    request.META['SERVER_NAME'] = 'youpi.youpla'
    return request

def createUser(pwd='toto'):
    today = datetime.date.today()
    user = User(username='dummy',email='dummy@domain.tld',
               last_login=today, date_joined=today, is_active=True )
    user.set_password(pwd)
    user.save()
    return user

class FormsTest(TestCase):
    fixtures = ['test/auser.yaml',]
    def setUp(self):
        pass

    def testLoginForm(self):
        """Check login form
        """
        # Forget user
        f1 = LoginForm({'pw':'test'})
        self.assertEqual(f1.is_valid(), False)
        self.assertEqual(f1.errors['__all__'][0], _("Email or password incorrect").translate('en'))
        # Forget password
        f1 = LoginForm({'email':'test'})
        self.assertEqual(f1.is_valid(), False)
        self.assertEqual(f1.errors['__all__'][0], _("Email or password incorrect").translate('en'))
        # Unexistant email
        f1 = LoginForm({'email':'zzzzzz@a.fr', 'pw':'test'})
        self.assertEqual(f1.is_valid(), False)
        self.assertEqual(f1.errors['__all__'][0], _("Email or password incorrect").translate('en'))
        # Incorrect
        f1 = LoginForm({'email':'a@a.fr', 'pw':'test'})
        self.assertEqual(f1.is_valid(), False)
        self.assertEqual(f1.errors['__all__'][0], _("Email or password incorrect").translate('en'))
        # correct
        f1 = LoginForm({'email':'a@a.fr','pw':'toto'})
        self.assertEqual(f1.is_valid(), True)
        # not active
        auser = User.objects.get(email='a@a.fr')
        auser.is_active = False
        auser.save()
        f1 = LoginForm({'email':'a@a.fr','pw':'toto'})
        self.assertEqual(f1.errors['__all__'][0], _("This user is not active").translate('en'))

class UserTest(TestCase):
    fixtures = ['test/auser.yaml',]
    username = 'dummy'
    email = 'a@a.fr'
    password = 'toto'
    def setUp(self):
        pass
    def testFixture(self):
        """Test... testsuite
        """
        User.objects.get(username='dummy')
        Identity.objects.get(username='dummy')

    def testAnnonURLs(self):
        """Test all urls in Annonymous mode
        """
        response = self.client.get('/account/create')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].has_key('loginform'), True)
        response = self.client.get('/account/login')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context[0].has_key('loginform'), True)
        response = self.client.get('/account/logout')
        self.assertRedirects(response, '/account/login?next=/account/logout')
        response = self.client.get('/account/identities/')
        self.assertRedirects(response, '/account/login?next=/account/identities/')
        response = self.client.get('/account/identities/dummy')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/identities/dummy/modify')
        self.assertRedirects(response, '/account/login?next=/account/identities/dummy/modify')
        response = self.client.get('/account/identities/dummy/new')
        self.assertRedirects(response, '/account/login?next=/account/identities/dummy/new')
        response = self.client.get('/account/identities/dummy/delete')
        self.assertRedirects(response, '/account/login?next=/account/identities/dummy/delete')
        response = self.client.get('/account/')
        self.assertRedirects(response, '/account/login?next=/account/')
        response = self.client.get('/account/edit')
        self.assertRedirects(response, '/account/login?next=/account/edit')
        response = self.client.get('/account/delete')
        self.assertRedirects(response, '/account/login?next=/account/delete')
        # Ident deactivated
        response = self.client.get('/dommj')
        self.assertEqual(response.status_code, 404)

    def testURLs(self):
        """Test all URLs when loggued in
        """
        self.client.login(username='dummy', password='toto')
        response = self.client.get('/account/create')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/login')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/identities/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/identities/dummy')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/identities/dummy/modify')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/identities/dummy/new')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/identities/dummy/delete')
        self.assertEqual(response.status_code, 404) # Not implemented
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/edit')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/delete')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/account/logout')
        self.assertRedirects(response, reverse("home"))
        # Ident deactivated
        response = self.client.get('/account/identities/dommj')
        self.assertEqual(response.status_code, 404)

    def testLogin(self):
        """Test login/logout chain
        """
        response = self.client.get('/account/')
        self.assertRedirects(response, '/account/login?next=/account/')
        response = self.client.get('/account/login')
        self.assertTemplateUsed(response, 'account/login.html')
        # With incorrect credentials
        credentials = {'email' : self.email, 'pw' : 'notgood'}
        response = self.client.post('/account/login', credentials)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', '', _("Email or password incorrect"))
        self.assertContains(response, "Email or password incorrect")
        self.assertNotEqual(response.client.session.get('_auth_user_id'), 1)
        # With correct credentials
        credentials = {'email' : self.email, 'pw' : self.password}
        response = self.client.post('/account/login', credentials)
        self.assertRedirects(response, '/account/')
        self.assertEqual(response.client.session.get('_auth_user_id'), 1)
        # I'm NOT loggued right?
        response = self.client.get('/account/')
        self.assertContains(response, self.email)
        self.assertContains(response, reverse('logout'))
        # Try to login again
        response = self.client.get('/account/login', credentials)
        self.assertTemplateUsed(response, 'account/error.html')
        # Log out now...
        response = self.client.get('/account/logout')
        self.assertRedirects(response, reverse("home"))
        self.assertNotEqual(response.client.session.get('_auth_user_id'), 1)
        # Try next statement in URL
        response = self.client.get('/account/login', {'next':'/account/identities/'})
        self.assertContains(response, '/account/identities/')
        credentials['next'] = '/account/identities/'
        response = self.client.post('/account/login', credentials)
        self.assertRedirects(response, '/account/identities/')
        # "None" bug when no next statement given to template
        response = self.client.get('/account/logout')
        response = self.client.get('/account/login',)
        self.assertContains(response, 'name="next" value="/account/"')

    def testConfirm(self):
        """Test confirmation email and link
        """
        # Set up and send confirm code
        request = dummyRequest()
        profile = UserProfile.objects.get(user__email=self.email)
        code = profile.generateconfirmcode()
        profile.save()
        profile.sendemail(request)

        # Checkmail
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue(profile.confirmcode in mail.outbox[0].body)
        self.assertTrue(reverse("confirm", kwargs={ 'code': code }) in mail.outbox[0].body)
        host = "%s://%s" % ("https", request.META["SERVER_NAME"])
        self.assertTrue(host in mail.outbox[0].body)

        # Confirm code for already active user : Error
        profile.user.is_active = True
        profile.user.save()
        response = self.client.get(reverse('confirm', kwargs={'code': code}))
        self.assertTemplateUsed(response, 'account/confirm.html')
        self.assertTrue("Error" in response.content)

        # Now activate user
        profile.user.is_active = False
        profile.user.save()
        response = self.client.get(reverse('confirm', kwargs={'code': code}))
        self.assertTemplateUsed(response, 'account/confirm.html')
        self.assertTrue(reverse("home") in response.content)
        self.assertEqual(response.client.session.get('_auth_user_id'), 1)
        self.assertTrue(UserProfile.objects.get(user__email=self.email).user.is_active)

    def testIdentAdd(self):
        """Test identity add chain
        """
        self.client.login(username=self.email, password=self.password)
        response = self.client.post('/account/', {"newid" : "dummy"})
        self.assertTemplateUsed(response, 'account/dashboard.html')
        response = self.client.post('/account/', {"newid" : "dummy3"})
        self.assertRedirects(response, '/account/identities/dummy3/new')

        # Don't show is_active field !
        response = self.client.get('/account/identities/dummy3/new')
        self.assertNotContains(response, 'is_active')

        # With existing user data
        credentials = {'first_name' : "something", 'email' : "a@a.fr"}
        response = self.client.post('/account/identities/dummy/new', credentials)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/create.html')
        self.assertEqual(response.context[0]['error'], 'exist')

        # With another identity
        credentials = {'first_name' : "something", 'email' : "a@a.fr"}
        response = self.client.post('/account/identities/dummy2/new', credentials)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/create.html')
        self.assertEqual(response.context[0]['error'], 'notmine')

        # With correct data
        credentials = {'first_name' : "something", 'email' : "aaa@aaa.fr"}
        response = self.client.post('/account/identities/dummy3/new', credentials)
        ident = Identity.objects.get(userid='dummy3', is_active=True)
        IdentityPerms.objects.get(identity=ident)
        self.assertRedirects(response, '/account/identities/dummy3')

    def testIdentModify(self):
        """Test modify chain of identities
        """
        self.client.login(username=self.email, password=self.password)

        # Don't show is_active field !
        response = self.client.get('/account/identities/dummy/modify')
        self.assertNotContains(response, 'is_active')

        # Ident Don't exist
        credentials = {'first_name' : "something", 'email' : "a@a.fr"}
        response = self.client.post('/account/identities/dummy3/modify', credentials)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/modify.html')
        self.assertEqual(response.context[0]['error'], 'dontexist')

        # Ident not mine
        credentials = {'first_name' : "something", 'email' : "a@a.fr"}
        response = self.client.post('/account/identities/dummy2/modify', credentials)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/modify.html')
        self.assertEqual(response.context[0]['error'], 'notmine')
        # Ident correct
        response = self.client.get('/account/identities/dummy/modify')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('a@a.fr' in response.content)

        credentials = {'email' : "b@b.fr"}
        response = self.client.post('/account/identities/dummy/modify', credentials)
        self.assertRedirects(response, '/account/identities/dummy')
        self.assertEqual(Identity.objects.get(userid="dummy").email, "b@b.fr")

    def testIdentList(self):
        """Test list of identities
        """
        self.client.login(username=self.email, password=self.password)
        idents = Identity.objects.filter(userprofile__user__username="dummy",
                                         is_active=True)
        nidents = Identity.objects.filter(userprofile__user__username="dummy",
                                         is_active=False)
        response = self.client.get('/account/identities/')
        self.assertEqual(response.status_code, 200)
        for ident in idents:
            self.assertContains(response, ident.userid)
            self.assertContains(response, reverse("identedit", kwargs={'userid' : ident.userid}))
        for ident in nidents:
            self.assertNotContains(response, ident.userid)
            self.assertNotContains(response, reverse("identedit", kwargs={'userid' : ident.userid}))
        self.assertTemplateUsed(response, 'account/identities/list.html')

    def testIdentShow(self):
        """Test identity detail
        """
        self.client.login(username=self.email, password=self.password)
        ident = Identity.objects.filter(userprofile__user__username="dummy")[0]
        assoc = TrustedConsumers(host="http://toto/", always=True, user=ident.userprofile.user, identity=ident)
        assoc.save()
        response = self.client.get(reverse("identshow", kwargs={'userid' : ident.userid}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ident.userid)
        self.assertContains(response, reverse("identrevokeassoc", kwargs={'userid' : ident.userid}))
        self.assertTemplateUsed(response, 'account/identities/show.html')

    def testAccountShow(self):
        """Test user dashboard
        """
        self.client.login(username=self.email, password=self.password)
        response = self.client.get('/account/')
        idents = Identity.objects.filter(userprofile__user__username="dummy", is_active=True)
        for ident in idents:
            self.assertContains(response, ident.userid)
            self.assertContains(response, reverse("identshow", kwargs={'userid' : ident.userid}))
        self.assertContains(response, reverse("identlist", ))
        self.assertTemplateUsed(response, 'account/dashboard.html')

    def testAccountHistory(self):
        """Test user history
        """
        from account.models import RPHistory
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(reverse('accounthistory'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, RPHistory.objects.get(pk=1).host)
        # TODO : test pagination ?

    def testAccountEdit(self):
        """Test edit existant account
        """
        self.client.login(username=self.email, password=self.password)
        response = self.client.get(reverse("accountedit"))
        self.assertTemplateUsed(response, 'account/edit/edit.html')
        self.assertContains(response, self.email )
        self.assertContains(response, reverse("accounteditemail"))
        self.assertContains(response, reverse("accounteditpasw"))

    def testAccountEditEmail(self):
        """Test email change
        """
        self.client.login(username=self.email, password=self.password)
        email = 'r@a.fr'
        response = self.client.get(reverse("accounteditemail"))
        self.assertTemplateUsed(response, 'account/edit/form.html')
        self.assertContains(response, self.email )
        response = self.client.post(reverse("accounteditemail"), {'email' : email})
        self.assertContains(response, email )
        response = self.client.post(reverse("accounteditemail"), {'email' : email, 'email_c' : email})
        self.assertRedirects(response, reverse("accounteditemailok"))
        response = self.client.get(reverse("accounteditemailok"))
        self.assertEqual(response.status_code, 200)
        self.assertRaises(User.DoesNotExist, User.objects.get, email=self.email)
        user = User.objects.get(email=email)
        self.assertFalse(user.is_active)
        self.assertEquals(len(mail.outbox), 1)

    def testAccountEditPasw(self):
        """Test password change
        """
        self.client.login(username=self.email, password=self.password)
        paswd = 'moo'
        response = self.client.get(reverse("accounteditpasw"))
        self.assertTemplateUsed(response, 'account/edit/form.html')
        response = self.client.post(reverse("accounteditpasw"), {'pw1' : paswd})
        self.assertContains(response, 'moo' )
        response = self.client.post(reverse("accounteditpasw"), {'pw1' : paswd, 'pw2' : paswd})
        self.assertRedirects(response, reverse("accounteditpaswok"))
        response = self.client.get(reverse("accounteditpaswok"))
        self.assertEqual(response.status_code, 200)
        # Logout and test our new password
        self.client.logout()
        self.client.login(username=self.email, password=paswd)
        response = self.client.get(reverse("accounteditpasw"))
        self.assertEqual(response.status_code, 200)

    def testIdentShowAnnonymous(self):
        """Annonymous identities views
        """
        #self.fail('TestSuite not ready')
        exist = Identity.objects.get(pk=1)
        # Don't exist
        response = self.client.get('/account/identities/dummy3')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/dummy3')
        self.assertEqual(response.status_code, 404)
        # Deactivated
        response = self.client.get('/account/identities/dommj')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/dommj')
        self.assertEqual(response.status_code, 404)
        # Exist
        response = self.client.get('/account/identities/%s' % exist.userid)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/show.html')
        self.assertNotContains(response, '/account/identities/dummy/modify' )
        self.assertContains(response, 'showtoall' )
        self.assertNotContains(response, 'showtome' )

    def testIdentShowLogued(self):
        """Logged-in identities views
        """
        self.client.login(username=self.email, password=self.password)
        notmine = Identity.objects.get(pk=2)
        mine = Identity.objects.get(pk=1)
        # Don't exist
        response = self.client.get('/account/identities/dummy3')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/blank.html')
        self.assertContains(response, '/account/identities/dummy3/new')
        self.assertContains(response, 'dummy3')
        response = self.client.get('/dummy3')
        self.assertEqual(response.status_code, 404)
        #self.assertContains(response, reverse('identcreate', kwargs={'userid' : 'dummy3'}))
        # Not Mine
        response = self.client.get('/account/identities/%s' % notmine.userid)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/show.html')
        self.assertContains(response, 'showtoall' )
        self.assertNotContains(response, 'showtome' )
        # Mine
        response = self.client.get('/account/identities/dummy')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/identities/show.html')
        self.assertContains(response, '/account/identities/dummy/modify' )
        # self.assertContains(response, '/account/identities/dummy/delete' )
        self.assertContains(response, 'showtoall' )
        self.assertContains(response, 'showtome' )
        # Deactivated
        response = self.client.get('/account/identities/dommj')
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/dommj')
        self.assertEqual(response.status_code, 404)

class NoFixturesTest(TestCase):
    def testSameUserID(self):
        """From #108
        """
        # Create User
        request = dummyRequest()
        email = "amail@amil.com"
        pwd = "pwd"
        udata= {"username" : email}
        sdata = {"email" : email,
                 "email_c" : email,
                 "pw1" : pwd,
                 "pw2" : pwd}
        wiz = SubscribeWizard([SubscribeForm, CaptchaForm ,UsernameForm])
        user = wiz.create_user([sdata, udata], request)
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 302)
        self.assertFalse(user.is_active)
        user.is_active = True
        user.save()
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 302)
        self.client.login(username=email, password=pwd)
        response = self.client.get('/account/')
        self.assertEqual(response.status_code, 200)
