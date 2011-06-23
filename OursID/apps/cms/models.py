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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from datetime import datetime
from django.db.models import permalink
from django.contrib.auth.models import User

import mptt

from managers import PageManager
# Create your models here.

DEFAULT_LANGUAGE='en'

class Language(models.Model):
    """Language code for pages
    """
    code = models.CharField(_("Code"), max_length=6, unique=True)
    name = models.CharField(_("Name"), max_length=15)

    def __unicode__(self):
        return self.code

class Page(models.Model):
    """A page is an entry in CMS tree
    Linked by a localized content
    """
    # Base
    DRAFT = 0
    PUBLISHED = 1
    WAIT = 2
    STATUSES = [
        (DRAFT, _('Draft')),
        (PUBLISHED, _('Published')),
        (WAIT, _('Waiting')),
        ]
    TYPE_CATEGORY = 0
    TYPE_BLOG = 1
    FOLDER_TYPES = [
                (TYPE_CATEGORY, 'Category'),
                (TYPE_BLOG, 'Blog'),
                ]
    _lang = DEFAULT_LANGUAGE # "Cached" value for Lang
    author = models.ForeignKey(User, verbose_name=_("Author"), null=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    title = models.CharField(_("Title"), max_length=70, help_text=_("default title of page"))
    slug = models.SlugField(_("slug"), unique=True, help_text=_("default slug of page"))
    folder_type = models.IntegerField("Categorie", max_length=20, choices=FOLDER_TYPES, default=TYPE_CATEGORY)
    login_required = models.BooleanField(_('login required'), default=False)
    in_navigation = models.BooleanField(_("in navigation"), default=True)
    template = models.CharField(_("template"), max_length=100, default='', blank=True, help_text="(not ready)")
    redirects = models.CharField(_("redirects"), max_length=100, default='', blank=True, help_text=_("If not empty, redirect to this url"))
    publish_state = models.IntegerField(_("Publish state"), choices=STATUSES, default=DRAFT)
    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_('(not ready)'), db_index=True)
    created = models.DateTimeField(_("Creation date"), default=datetime.now)
    objects = PageManager()

    class Meta:
        ordering = ( 'tree_id', 'lft')
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        unique_together = ('parent', 'slug')

    def __unicode__(self):
        title = self.title
        if self.parent:
            title = self.parent.__unicode__() + " / " + title
        return title

    def get_path(self, language=None):
        """Give path of object
        """
        ancestors = list(self.get_ancestors()) + [self,]
        if not language:
            language = self._lang
        tree = ( x.get_slug(language) for x in ancestors )
        path = "/".join(tree)
        return path

    def get_languages(self):
        """get the list of all existing languages for this page
        """
        contents = Content.objects.filter(page=self)
        languages = set(x.language for x in contents)
        return list(languages)

    def get_content(self, language=None):
        """Return content if a content is available in language
        else return None
        """
        if not language:
            language = self._lang

        # A kind of cache
        if language == self._lang and hasattr(self, "content_cache"):
            return self.content_cache

        result = False
        try:
            contents = Content.objects.get(page=self, language__code=language)
        except Content.DoesNotExist:
            result = None
        else:
            result = contents

        # Store for artisanal cache
        if language == self._lang and not hasattr(self, "content_cache"):
            self.content_cache = result

        return result

    def get_slug(self, language=None):
        """Get slug of object in language if any
        """
        if not language:
            language = self._lang
        content = self.get_content(language)
        if content:
            if len(content.slug):
                return content.slug
        return self.slug

    def get_title(self, language=None):
        """Get title of object in language if any
        """
        if not language:
            language = self._lang
        content = self.get_content(language=None)
        if content:
            if len(content.title):
                return content.title
        return self.title

    def set_lang(self, language):
        """Set lang variable
        """
        self._lang = str(language)

        # regen 'cache'
        if hasattr(self, "content_cache"):
            delattr(self, "content_cache")
        self.content_cache = self.get_content(self._lang)
        return self

    @permalink
    def get_absolute_url(self, language=None):
        """Return Permalink
        """
        if not language:
            language = self._lang
        return ("cmspage", (), { 'url' :  self.get_path(language), 'lang' : language })

# Don't register the Page model twice.
try:
    mptt.register(Page)
except mptt.AlreadyRegistered:
    pass

class Content(models.Model):
    """i18n content for a Page

    >>> p = Page(title="onetest", slug="onetest")
    >>> l = Language(code="fr", name="fr")
    >>> p.save()
    >>> l.save()
    >>> c = Content(language=l, page=p, slug='foobar', )
    >>> c.save()

    # Try to register two contents with samelanguages
    >>> c = Content(language=l, page=p,)
    >>> c.save()
    Traceback (most recent call last):
        ...
    IntegrityError: columns language_id, page_id are not unique

    """
    HTML = 0
    FORMATS = [
        (HTML, _("HTML")),
        ]
    format = models.IntegerField(_("content format"), choices=FORMATS, default=HTML )
    title = models.CharField(_("title"), max_length=70, help_text=_("Enter title here to overide page's default"), blank=True)
    slug = models.SlugField(_("url"), help_text=_("Enter slug here to overide page's default"), blank=True)
    language = models.ForeignKey(Language, verbose_name=_("language")) 
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="content_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    description = models.TextField(_("description"), default='', blank=True, help_text=_("Few words."))
    body = models.TextField(_("body"), blank=True, help_text=_("Content of page"))

    class Meta:
        unique_together = (('language', 'page'),)

    def get_title(self):
        """Return self's title if provided or parent's title
        """
        if len(self.title):
            return self.title
        return self.page.title

    def get_slug(self):
        """Return self's slug if provided or parent's slug
        """
        if len(self.slug):
            return self.slug
        return self.page.slug

    @permalink
    def get_absolute_url(self):
        """Return Permalink
        """
        return ("cmspage", (), { 'url' : self.page.get_path(self.language.code), 'lang' : self.language.code })

    def __unicode__(self):
        return self.get_title()

