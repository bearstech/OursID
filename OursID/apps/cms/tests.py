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

from django.test import TestCase

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from django.utils.translation import ugettext_lazy as _

from django.core.urlresolvers import reverse

from models import Page

def createUser(pwd='toto'):
    today = datetime.date.today()
    user = User(username='dummy',email='dummy@domain.tld',
               last_login=today, date_joined=today, is_active=True, is_staff=True)
    user.set_password(pwd)
    user.save()
    return user

def urlpage(url, lang='fr'):
    """Reverse for a cms page
    """
    return reverse("cmspage", kwargs={'url' : url, 'lang' : lang})

def urlblog(url,page=1, lang='fr'):
    """Reverse for a paginated blog page
    """
    return reverse("cmsblogpage", kwargs={'url' : url, 'lang' : lang,'page': page })

class TemplateTest(TestCase):
    """Test articles representation

    DB organisation :
        - Categ_1 ( Art_11, Art_12, Cat_13 ( Art_131, Art_132 ) )
        - Categ_2 ( Blog_21 ( Art_211, Art_212 ) )
        - Art_3

    All articles have an '*-fr' Content (language='fr')
    Categ_1 also have an 'deutch' Content (language='de')
    """
    fixtures = ['cms.yaml',]
    def setUp(self):
        """Get somes objects to help tests
        """
        self.categ1 = Page.objects.get(slug="categ_1")
        self.art11 = Page.objects.get(slug="art_11")
        self.art12 = Page.objects.get(slug="art_12")
        self.categ2 = Page.objects.get(slug="categ_2")
        self.categ13 = Page.objects.get(slug="categ_13")
        self.blog21 = Page.objects.get(slug="blog_21")
        self.art211 = Page.objects.get(slug="art_211")
        self.art212 = Page.objects.get(slug="art_212")

    def testURLs(self):
        """Test models's permalink
        """
        self.assertEqual(self.categ1.get_absolute_url(), urlpage("categ_1-fr"))
        self.assertEqual(self.art11.get_absolute_url(), urlpage("categ_1-fr/art_11-fr"))
        self.assertEqual(self.categ13.get_absolute_url(), urlpage("categ_1-fr/categ_13-fr"))
        self.assertEqual(self.categ2.get_absolute_url(), urlpage("categ_2-fr"))
        self.assertEqual(self.blog21.get_absolute_url(), urlpage("categ_2-fr/blog_21-fr"))
        self.assertEqual(self.art211.get_absolute_url(), urlpage("categ_2-fr/blog_21-fr/art_211-fr"))
        self.assertEqual(self.art211.set_lang('de').get_absolute_url(), urlpage("categ_2/blog_21/art_211", 'de'))

    def testManager(self):
        """Test Page's model manager
        """
        page = Page.objects.get_lslug(slug="art_11")
        self.assertEqual(page, self.art11)
        # TODO !

    def testLangRedirect(self):
        """Test redirection if language not in URL
        """
        start = reverse("nolang", kwargs={ 'url' : 'categ_1-fr'})
        expected = urlpage('categ_1-fr')
        response = self.client.get(start)
        self.assertRedirects(response, expected, status_code=301)

    def test404s(self):
        """Test some wrongs URLs
        """
        response = self.client.get(urlpage("ca_1/categ_13"))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(urlpage("ca_1/art11"))
        self.assertEqual(response.status_code, 404)

    def testArticle(self):
        """Test some articles
        """
        # TODO !

    # General tests
    # (view + template)
    def testCategory(self):
        """Test view and template of a category

        We test Categ_1, it must have all content (body + description)
        Children must have description
        Both must have title and href
        Finally, a link to all translated Contents must be present
        """
        response = self.client.get(self.categ1.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cms/category.html')
        # Categ1 must have all content ( description + body)
        self.assertContains(response, self.categ1.get_title())
        self.assertContains(response, self.categ1.get_content().description)
        self.assertContains(response, self.categ1.get_content().body)
        self.assertContains(response, self.categ1.get_absolute_url())
        # Childs just have description
        self.assertContains(response, self.art11.get_title())
        self.assertContains(response, self.art11.get_content().description)
        self.assertNotContains(response, self.art11.get_content().body)
        self.assertContains(response, self.art11.get_absolute_url())
        self.assertContains(response, self.art12.get_title())
        self.assertContains(response, self.art12.get_content().description)
        self.assertNotContains(response, self.art12.get_content().body)
        self.assertContains(response, self.art12.get_absolute_url())
        self.assertContains(response, self.categ13.get_title())
        self.assertContains(response, self.categ13.get_content().description)
        self.assertNotContains(response, self.categ13.get_content().body)
        self.assertContains(response, self.categ13.get_absolute_url())
        # Translated link
        self.assertContains(response, self.categ1.get_absolute_url(language='de'))

    def testCategory_i18n(self):
        """Test category in other language

        Test deutch content of categ_1
        """
        response = self.client.get(self.categ1.get_absolute_url(language='de'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cms/category.html')
        # Translated link
        self.assertContains(response, self.categ1.get_absolute_url())

    def testBlog(self):
        """Test view and template of a category

        We test Blog_21, it must have all content (body + description)
        Children must have description and body
        Both must have title and href
        """
        response = self.client.get(self.blog21.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cms/blog.html')
        # Blog
        self.assertContains(response, self.blog21.get_title())
        self.assertContains(response, self.blog21.get_content().description)
        self.assertContains(response, self.blog21.get_content().body)
        # Childs
        self.assertContains(response, self.art211.get_absolute_url())
        self.assertContains(response, self.art211.get_title())
        self.assertContains(response, self.art211.get_content().description)
        self.assertContains(response, self.art211.get_content().body)
        self.assertContains(response, self.art212.get_absolute_url())
        self.assertContains(response, self.art212.title)
        self.assertContains(response, self.art212.get_content().body)
        self.assertContains(response, self.art212.get_content().description)

    def testBlogPaginate(self):
        """Test view and template of a paginated blog
        Must have :
            - "Previous" link
            - "Next" link
            - Antichronological order

        """
        # Populate blog with temporary content
        temp = []
        for i in range(30):
            a = Page(title="temp_%s" % i, slug="temp-%s" % i, parent=self.blog21, folder_type=0, publish_state=Page.PUBLISHED )
            a.save()
            temp += [a]
        # Test Page 1
        response = self.client.get(urlblog('categ_2-fr/blog_21-fr', 1))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, temp[29].get_title())
        self.assertContains(response, urlblog('categ_2-fr/blog_21-fr', 2)) # Previous link
        self.assertNotContains(response, temp[1].get_title())
        # Test page 3
        response = self.client.get(urlblog('categ_2-fr/blog_21-fr', 3))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, urlblog('categ_2-fr/blog_21-fr', 2)) # Previous link
        self.assertContains(response, urlblog('categ_2-fr/blog_21-fr', 4)) # Next Link
        self.assertNotContains(response, temp[29].get_title())
        self.assertContains(response, temp[19].get_title())

    def testRedirects(self):
        """Test redirects fields

        Test absolute and relative redirections
        """
        # Relative
        expected = self.categ2.get_absolute_url()
        self.categ1.redirects = expected
        self.categ1.save()
        response = self.client.get(self.categ1.get_absolute_url())
        self.assertRedirects(response, expected, status_code=301)
        # Absolute
        expected = "http://bearstech.com"
        self.art211.redirects = expected
        self.art211.save()
        response = self.client.get(self.art211.get_absolute_url())
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['Location'], expected)

    def testTemplate(self):
        """Test custom template field
        """
        template = 'dummy.html'
        self.categ1.template = template
        self.categ1.save()
        response = self.client.get(self.categ1.get_absolute_url())
        self.assertTemplateUsed(response, template)

    def testRootPage(self):
        """ Test Root Page
        """
        response = self.client.get(reverse('cmsroot', kwargs={'lang':'fr'}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cms/root.html')
        # root
        self.assertContains(response, self.categ1.get_title())
        self.assertContains(response, self.categ1.get_absolute_url())
        self.assertContains(response, self.categ1.get_content().description)
        self.assertContains(response, self.categ2.get_title())
        self.assertContains(response, self.categ2.get_absolute_url())
        self.assertContains(response, self.categ2.get_content().description)
