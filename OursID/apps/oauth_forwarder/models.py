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
from account.models import UserProfile

class OAuthRequest(models.Model):
    """OAuth authentification requests
    - validation:
        0 pending
        1 refused
        2 accepted
    """
    VALIDATION_PENDING = 0
    VALIDATION_REFUSED = 1
    VALIDATION_ACCEPTED = 2
    
    oauth_url = models.TextField()
    oauth_callback = models.TextField()
    date_created = models.DateTimeField()
    userprofile = models.ForeignKey(UserProfile, unique=False, null=False)
    validation = models.IntegerField(null=False, default=VALIDATION_PENDING)
