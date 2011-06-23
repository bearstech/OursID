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
from models import Identity, IdentityPerms, UserProfile, IdentityPortrait

class IdentityPermsInline(admin.TabularInline):
    model = IdentityPerms
    #max_num = 1

class IdentityAdmin(admin.ModelAdmin):
    list_display = ('userid','username','email', )
    inlines = [ IdentityPermsInline, ]
    fieldsets = [
    ("Base", {'fields' : (('userid', 'userprofile') )}),
    ("Identity", {'fields' : (('username', 'email'), ('first_name', 'last_name'), ('dob',), ('is_active',),
                 ('adress',), ('zipcode', 'city', 'country'),)}),
                ]


class UserProfileAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Identity, IdentityAdmin)
admin.site.register(IdentityPortrait)
