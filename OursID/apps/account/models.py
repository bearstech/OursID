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

from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from settings import DEFAULT_FROM_EMAIL
from photologue.models import ImageModel
from random import choice
GENDER = [("M",_("Male")),("F",_("Female")),]

class UserProfile(models.Model):
    """Extends User account with some additionals fields
    """
    NOT_REGISTERED_NOTIFICATION_STATE = 0
    INVALID_REGISTRATION_NOTIFICATION_STATE = 1
    VALID_NOTIFICATION_STATE = 2
    NOTIFICATION_STATE_CHOICES = ((VALID_NOTIFICATION_STATE, 'Notification enabled'), (INVALID_REGISTRATION_NOTIFICATION_STATE, 'Invalid notification state'), (NOT_REGISTERED_NOTIFICATION_STATE, 'Notification not registered'))
    
    NONE_NOTIFICATION_TYPE = 0
    C2DM_NOTIFICATION_TYPE = 1
    JABBER_NOTIFICATION_TYPE = 2
    NOTIFICATION_TYPE_CHOICES = ((NONE_NOTIFICATION_TYPE, 'No Notification'), (C2DM_NOTIFICATION_TYPE, 'Google C2DM Notification'), (JABBER_NOTIFICATION_TYPE, 'Jabber Notification'))
    
    
    confirmcode = models.CharField(_('Confirm code'), unique=True, max_length=65)
    notification_type = models.IntegerField(choices=NOTIFICATION_TYPE_CHOICES, default=NONE_NOTIFICATION_TYPE)
    notification_id = models.CharField(max_length=1024, unique=False, null=False)
    notification_state = models.IntegerField(choices=NOTIFICATION_STATE_CHOICES, default=NOT_REGISTERED_NOTIFICATION_STATE)
    notification_oauth_enabled = models.BooleanField(null=False, default=True)
    user = models.ForeignKey(User, unique=True)

    def __unicode__(self):
        return self.user.email

    def generateconfirmcode(self):
        """Generate confirm code
        """
        ok = False
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        while not ok:
            confirm = "".join(choice(chars) for x in range(64))
            try :
                UserProfile.objects.get(confirmcode=confirm)
            except UserProfile.DoesNotExist :
                ok = True
            else :
                pass
        self.confirmcode = confirm
        return self.confirmcode

    def sendemail(self, request):
        """Send email with confirmation code
        """
        from django.core.mail import send_mail
        from django.template.loader import render_to_string

        proto = request.META.get('SERVER_PROTOCOL', 'http')
        if 'HTTPS' in proto:
            proto = 'https'
        else:
            proto = 'http'
        result = {}
        result['confirmcode'] =  self.confirmcode
        result["proto"] = proto
        result["sname"] = request.META.get('SERVER_NAME', 'invalid')

        subject = _('OPENID : confirmation')
        fromfield = DEFAULT_FROM_EMAIL
        to = self.user.email

        content = render_to_string('account/confirm.txt', result)
        send_mail(subject, content, fromfield, [to,], fail_silently=True)

    def confirm(self):
        """Verify code and set user's account active
        """
        self.user.is_active = True
        self.user.save()
        return

class Identity(models.Model):
    """Informations of a openid identity
    """
    userid = models.SlugField(_('UserID'), max_length=30, unique=True)
    username = models.CharField(_('Username'), max_length=30, blank=True)
    first_name = models.CharField(_('First name'), max_length=30, blank=True)
    last_name = models.CharField(_('Last name'), max_length=30, blank=True)
    email = models.EmailField(_('Email'),)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    dob = models.DateField(_('Date of birth'), blank=True, null=True, help_text="YYYY-MM-DD")
    adress = models.CharField(_('Adress'), max_length=100, blank=True)
    zipcode = models.CharField(_('ZIP Code'), max_length=10, blank=True)
    city = models.CharField(_('City'), max_length=20, blank=True)
    country = models.CharField(_('Country'), max_length=20, blank=True)#TODO : changer par liste
    gender = models.CharField(_('Gender'), max_length=1, blank=True, choices=GENDER)#TODO : changer par liste
    userprofile = models.ForeignKey(UserProfile)
    is_active = models.BooleanField(_('Is Active?'), default=True)

    def __unicode__(self):
        return self.userid

    def getsreg(self):
        sreg_data = {
            'fullname': u'%s %s' % (self.first_name, self.last_name ),
            'nickname': self.username,
            'dob': str(self.dob),
            'email': self.email,
            'gender': self.gender,
            'postcode': self.zipcode,
            'country': 'FR',
            'language': 'fr',
            'timezone': 'Europe/Paris',
            }
        return sreg_data

class IdentityPerms(models.Model):
    """Display permissions of an openid identity
    """
    sh_username = models.BooleanField(_('Display username?'), default=False)
    sh_first_name = models.BooleanField(_('Display first name?'), default=False)
    sh_last_name = models.BooleanField(_('Display last name?'), default=False)
    sh_email = models.BooleanField(_('Display email?'), default=False)
    sh_phone = models.BooleanField(_('Display phone?'), default=False)
    sh_adress = models.BooleanField(_('Display adress?'), default=False)
    sh_zipcode = models.BooleanField(_('Display ZIP Code?'), default=False)
    sh_city = models.BooleanField(_('Display city?'), default=False)
    sh_country = models.BooleanField(_('Display country?'), default=False)
    sh_avatar = models.BooleanField(_('Display avatar?'), default=False)
    sh_gender = models.BooleanField(_('Display gender?'), default=False)
    sh_dob = models.BooleanField(_('Display date of birth?'), default=False)
    identity = models.ForeignKey(Identity, unique=True)

    def __unicode__(self):
        return self.identity.userid + " Perms"

class IdentityPortrait(ImageModel):
        identity = models.OneToOneField(Identity, primary_key=True)

class RPHistory(models.Model):
    """Show history of athentications for a user
    """
    date = models.DateTimeField(_('Date'), auto_now=True)
    identity = models.ForeignKey(Identity)
    ip = models.IPAddressField(_('IP'))
    host = models.URLField(_('Host'))
    rp = models.CharField(_('RP'), max_length=60)
    auth_result = models.BooleanField(_('Result'))

    def __unicode__(self):
        return "%s %s %s : %s" % (self.date, self.identity, self.host, str(self.auth_result))

    class Meta:
        ordering = ['-date']

class TrustedConsumers(models.Model):
    """List all trusted consumers
    """
    host = models.URLField(_('Host'))
    always = models.BooleanField(_('Trust'))
    user = models.ForeignKey(User)
    identity = models.ForeignKey(Identity)

    class Meta:
        unique_together = [("host","user"), ]

