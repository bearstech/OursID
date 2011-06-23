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
from django.db.models import Q


class PageManager(models.Manager):
    def filter_lslug(self, slug, lang='fr'):
        """Try to find a page with slug OR children slug
        """
        result = self.filter(slug=slug)
        if not len(result):
            from cms.models import Content
            result = Content.objects.filter(slug=slug, language__code=lang)
            if not len(result):
                raise Content.DoesNotExist
            # TODO : Why not a QuerySet ?
            result = [ x.page for x in result ]
        return result

    def get_lslug(self, slug, lang='fr'):
        # TODO : optimise and raise exception if multiple objects
        return self.filter_lslug(slug, lang)[0]
    '''
    def get_content(self, slug, lang='fr'):
        """Return content if a content is avaiable in language
        else raise DoesNotExist exception
        """
        try:
            contents = Content.objects.get(page=self, language=language)
        except Content.DoesNotExist:
            return False
        return True
       '''     
        
