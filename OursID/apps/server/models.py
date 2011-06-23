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
from account.models import Identity

class OidRequest(models.Model):
    """OpenId authentification requests (checkid_immediate or checkid_setup)
    - validation:
        0 pending
        1 refused
        2 accepted
        3 always accepted
    """
    VALIDATION_PENDING = 0
    VALIDATION_REFUSED = 1
    VALIDATION_ACCEPTED = 2
    VALIDATION_ALWAYS_ACCEPTED = 3
    openid_request = models.TextField()
    date_created = models.DateTimeField()
    identity = models.ForeignKey(Identity, unique=False, null=False)
    validation = models.IntegerField(null=False, default=VALIDATION_PENDING)
    trust_root = models.TextField()
    required_fields = models.TextField()
