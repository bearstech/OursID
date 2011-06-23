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

from django import forms
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

class EmailForm(forms.Form):
    """Form to forward oauth request
    """
    email = forms.EmailField(label=_('Email'), help_text=_('Enter the email used to register your account.'))
    
    def clean_email(self):
        """Check if email exists in User table
        """
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
            return email
        except User.DoesNotExist:
            raise forms.ValidationError(_("There's no account with this email !"))
