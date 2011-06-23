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
from django import template

register = template.Library()

from cms.models import Page

#@register.inclusion_tag('cms/menubar.html')
def menu_bar(lang, separator=None):
    result = {'nodes' : (x.set_lang(lang) for x in Page.tree.root_nodes())}
    if separator:
        result['separator'] = separator
    return result

register.inclusion_tag('cms/menubar.html')(menu_bar)
