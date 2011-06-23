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
# Create your views here.
import settings
from django.http import Http404
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.simple import redirect_to
from django.core.urlresolvers import reverse, NoReverseMatch

from models import Page, Content, Language

from django.core.exceptions import ObjectDoesNotExist


def blogview(request, blog, lang, page=1):
    """Show a blog and blog's articles
       Paginated : 5 articles per pages
    """
    result = {}

    childrens = []
    if request.user.is_authenticated():
        childrens = blog.get_children()
    else:
        childrens = blog.get_children().filter(publish_state=blog.PUBLISHED)

    # Change lang for entries and order
    childrens = [ x.set_lang(lang) for x in childrens.order_by('-created')]
    ancestors = [ x.set_lang(lang) for x in blog.get_ancestors() ]

    # Get traductions
    traductions = blog.content_set.exclude(language__code=lang)

    # Paginate
    paginator = Paginator(childrens, 5)
    try:
        page = paginator.page(page)
    except (EmptyPage, InvalidPage):
        page = paginator.page(paginator.num_pages)

    result["page"] = page
    result["childrens"] = childrens
    result["ancestors"] = ancestors
    result["myself"] = blog
    result["traductions"] = traductions
    result["lang"] = lang

    # Change template if requested
    template = 'cms/blog.html'
    if len(blog.template):
        template = blog.template

    return render_to_response(template, result, context_instance=RequestContext(request))

def categoryview(request, category, lang):
    """Show body of a category and
    title, links and description of childrens
    """
    result = {}
    childrens = []
    if request.user.is_authenticated():
        childrens = category.get_children()
    else:
        childrens = category.get_children().filter(publish_state=category.PUBLISHED)

    # Change lang for entries :
    childrens = [ x.set_lang(lang) for x in childrens]
    ancestors = [ x.set_lang(lang) for x in category.get_ancestors() ]

    # Get traductions
    traductions = category.content_set.exclude(language__code=lang)

    result["childrens"] = childrens
    result["ancestors"] = ancestors
    result["myself"] = category
    result["traductions"] = traductions
    result["lang"] = lang

    # Change template if requested
    template = 'cms/category.html'
    if len(category.template):
        template = category.template
    return render_to_response(template, result, context_instance=RequestContext(request))


def nolang(request, url):
    """No lang was given by user
    set one !
    """
    try:
        expected = reverse('cmspage', kwargs={'url' : url, 'lang' : request.LANGUAGE_CODE})
    except NoReverseMatch:
        expected = reverse('cmspage', kwargs={'url' : url, 'lang' : settings.LANGUAGE_CODE})
    return redirect_to(request, expected)

def rootpage(request, lang=None):
    """
    """
    result = {}
    if lang is None:
        lang = request.LANGUAGE_CODE
    categs = Page.objects.filter(parent=None)
    childrens = [ x.set_lang(lang) for x in categs ]
    # Get traductions
    traductions = [str(x.code) for x in Language.objects.all()]

    result["childrens"] = childrens
    result["traductions"] = traductions
    result["lang"] = lang

    return render_to_response("cms/root.html", result, context_instance=RequestContext(request))

def page(request, url, lang, page=1):
    """Select wich view to show
    """
    # Find corresponding page
    myself = None
    lastslug = url.split("/")[-1]
    try:
        pages = Page.objects.filter_lslug(lastslug, lang)
    except ObjectDoesNotExist:
        raise Http404

    for apage in pages:
        # Check path
        if url == apage.get_path(language=lang):
            myself = apage

    if not myself:
        # No page at this url
        raise Http404

    if len(myself.redirects):
        return redirect_to(request, myself.redirects)

    myself.set_lang(lang)

    # If an ancestor isn't published, all childrens was'nt Published
    if request.user.is_authenticated():
        # TODO : Permisions
        pass
    else:
        entries = myself.get_ancestors()
        for entry in entries:
            if entry.publish_state != entry.PUBLISHED:
                # Http404 or 401
                raise Http404

    # Select view with Pagetype
    if myself.folder_type == myself.TYPE_CATEGORY :
        return categoryview(request, myself, lang)
    elif myself.folder_type == myself.TYPE_BLOG :
        return blogview(request, myself, lang, page)

    result = {}
    if settings.DEBUG:
        # 'dummy' template is used for debug and dissociate
        # specials cases.
        return render_to_response('dummy.html', result, context_instance=RequestContext(request))

    raise Http404
