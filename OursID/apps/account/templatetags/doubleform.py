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
"""
Tag to superpose 2 fields from 2 forms on same line

 {% 2fields field form %}

"""


from django.template import Library

register = Library()

@register.inclusion_tag("account/identities/id_form.html")
def double_form(form1, form2, prefix="sh_", ignore=['is_active',]):
    result = []
    for field in form1:
        if field.name in ignore:
            continue
        result.append((field, form2['%s%s' % (prefix, field.name)]))
    return { 'doubleform' : result}

