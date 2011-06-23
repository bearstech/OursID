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
from django.contrib import admin
from models import Page, Content, Language

class PageInline(admin.StackedInline):
    prepopulated_fields = {"slug":('title',)}
    model = Content
    extra = 1
    fieldsets = [
    ("Base", {'fields' : (('title', 'slug'),('format', 'language'), )}),
    ("Content", {'fields' : (('description',), ('body',))}),
                ]

class PageAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug":('title',)}
    #list_display = ('__unicode__', 'parent')

    #list_display = ('userid','username','email', )
    inlines = [ PageInline, ]
    fieldsets = [
    ("Base", {'fields' : (('parent', 'author'),('title', 'slug'), ('folder_type','publish_state') )}),
    ("Settings", {'fields' : (('redirects', 'login_required', 'in_navigation'),
                ('publication_date', 'created'), ('template',)), 
                'classes' : ('collapse',)}),
                ]
    class Media:
        js = ('/media/cms/jquery/jquery.js',
            '/media/cms/wymeditor/jquery.wymeditor.js',
            '/media/cms/admin_textarea.js')



admin.site.register(Page, PageAdmin)
admin.site.register(Language)
