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
from django.contrib.formtools.wizard import FormWizard
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth import authenticate
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from account.models import User, Identity, UserProfile, IdentityPerms, slugify, IdentityPortrait
from settings import JABBER_ID

class DeleteForm(forms.Form):
    """Wait a word like "DELETE" to be valid

    # Try with any word:
    >>> f = DeleteForm({'confirm':'any'})
    >>> f.is_valid()
    False

    # Try with DELETE word:
    >>> f = DeleteForm({'confirm':'DELETE'})
    >>> f.is_valid()
    True
    """
    confirm = forms.CharField(_('Confirm'), help_text=_('Type DELETE here to confirm.'))

    def clean_confirm(self):
        confirm = self.cleaned_data['confirm']
        if confirm == _('DELETE'):
            return confirm
        else:
            raise forms.ValidationError(_('Confirmation incorrect'))

class SubscribeForm(forms.Form):
    """Form to create a user

    Check somes values like confirmation fields, on uniques fields in tables.

    # Good
    >>> data = {'email' : 'a@a.fr', 'email_c' : 'a@a.fr', 'pw1' : 'toto', 'pw2' : 'toto'}
    >>> SubscribeForm(data).is_valid()
    True

    # email differs
    >>> data['email_c'] = 'b@b.fr'
    >>> SubscribeForm(data).is_valid()
    False

    # password differs
    >>> data['pw2'] = 'truc'
    >>> SubscribeForm(data).is_valid()
    False

    """
    email = forms.EmailField(label=_('Email'), help_text=_('A confirmation mail will be sent to your email address.'))
    email_c = forms.EmailField(label=_('Email confirmation'), help_text=_('Please type again your email address here.'))
    pw1 = forms.CharField(label=_('Password'), help_text=_('Your password.'), widget=forms.PasswordInput)
    pw2 = forms.CharField(label=_('Password confirmation'), help_text=_('Please type again your password.'), widget=forms.PasswordInput)

    def clean_email(self):
        """Check if email is unique in User and Identity tables
        """
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(_("A user with that email already exists."))

    def clean_email_c(self):
        """Check if email confirmation field is same than email field
        """
        email = self.cleaned_data.get("email", "")
        email_c = self.cleaned_data["email_c"]

        if email == "":
            return email_c # Don't check while email isn't valid
        elif not email == email_c:
            raise forms.ValidationError(_("The two email fields didnt corresponds."))
        return email_c

    def clean_pw2(self):
        """Check if email confirmation field is same than email field
        """
        pw1 = self.cleaned_data.get("pw1", "")
        pw2 = self.cleaned_data["pw2"]

        if not pw1 == pw2:
            raise forms.ValidationError(_("The two password fields didnt corresponds."))
        return pw2

class UsernameForm(forms.Form):
    username = forms.CharField(label=_('Username'),max_length=30,  help_text=_('Name of your first openid identity.'))

    def clean_username(self):
        """Check if username is unique in User and Identity tables
        """
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            try :
                Identity.objects.get(userid=username)
            except Identity.DoesNotExist:
                return username
            else:
                raise forms.ValidationError(_("A user with that username already exists."))
        else:
            raise forms.ValidationError(_("A user with that username already exists."))

class SubscribeWizard(FormWizard):
    """ Wizard for new account

    The Captcha form can be validated only once. We use an ugly hack to store in
    session when captcha is valided on first validation
    """
    def done(self, request, form_list):
        """Ignore Captchaform because he's not valid
        """
        # Ignore captchaform !
        allforms = [form.cleaned_data for step, form in enumerate(form_list) if step in [0,2]]
        if request.session.get('captcha'):
            del request.session['captcha']

        user = self.create_user(allforms, request)
        return HttpResponseRedirect(reverse("accountcreateok"))

    def create_user(self, forms, request):
        """Create a user with content of the Form
        """
        subform = forms[0]
        userform = forms[1]
        user = User(username=userform['username'], email=subform['email'])
        user.set_password(subform['pw1'])
        user.is_active = False
        user.save()
        slug = slugify(userform['username'])
        profile = UserProfile(user=user)
        profile.generateconfirmcode()
        profile.save()
        ident = Identity(username=userform['username'], email=subform['email'], userid=slug, userprofile=profile)
        ident.save()
        identp = IdentityPerms(identity=ident)
        identp.save()
        profile.sendemail(request)
        return user

    def get_template(self, step):
        return 'account/home.html'

    def parse_params(self, request, *args, **kwargs):
        """Add client IP for reCPATCHA Form

        Reset session cookie for captcha just
        """
        current_step = self.determine_step(request, *args, **kwargs)
        if request.method == 'POST':
            initial = {'captcha' : request.META["REMOTE_ADDR"] }
            self.initial[1] = initial
            if current_step == 1:
                if request.session.get('captcha'):
                    del request.session['captcha']

    def render_revalidation_failure(self, request, step, form):
        """
        Hook for rendering a template if final revalidation failed.

        It is highly unlikely that this point would ever be reached, but See
        the comment in __call__() for an explanation.
        """
        # Validate all the forms. If any of them fail validation, that
        # must mean the validator relied on some other input, such as
        # an external Web site.
        num = self.num_steps()
        final_form_list = [self.get_form(i, request.POST) for i in range(num)]
        for i, f in enumerate(final_form_list):
            if isinstance(f, CaptchaForm) and request.session.get('captcha', None) is not None:
                # Captcha does not be revalidate
                pass
            elif not f.is_valid():
                return super(SubscribeWizard, self).render_revalidation_failure(request, i, f)
        return self.done(request, final_form_list)

    def security_hash(self, request, form):
        """
        Calculates the security hash for the given HttpRequest and Form instances.

        Subclasses may want to take into account request-specific information,
        such as the IP address.
        """
        from django.contrib.formtools.utils import security_hash
        if isinstance(form, CaptchaForm):
            return request.session.get('captcha', "error")

        return security_hash(request, form)

    def process_step(self, request, form, step):
        """
        Hook for modifying the FormWizard's internal state, given a fully
        validated Form object. The Form is guaranteed to have clean, valid
        data.

        This method should *not* modify any of that data. Rather, it might want
        to set self.extra_context or dynamically alter self.form_list, based on
        previously submitted forms.

        Note that this method is called every time a page is rendered for *all*
        submitted steps.
        """
        from random import randrange
        if isinstance(form, CaptchaForm):
            if not request.session.get('captcha'):
                request.session['captcha'] = str(randrange(1111111111,9999999999))

    def render_template(self, request, form, previous_fields, step, context=None):
        """
        Renders the template for the given step, returning an HttpResponse object.

        Override this method if you want to add a custom context, return a
        different MIME type, etc. If you only need to override the template
        name, use get_template() instead.

        The template will be rendered with the following context:
            step_field -- The name of the hidden field containing the step.
            step0      -- The current step (zero-based).
            step       -- The current step (one-based).
            step_count -- The total number of steps.
            form       -- The Form instance for the current step (either empty
                          or with errors).
            previous_fields -- A string representing every previous data field,
                          plus hashes for completed forms, all in the form of
                          hidden fields. Note that you'll need to run this
                          through the "safe" template filter, to prevent
                          auto-escaping, because it's raw HTML.
        """
        context = context or {}
        context.update(self.extra_context)

        # Hack to have "http(s)://host" on UsernameForm form (see #136)
        if isinstance(form, UsernameForm):
            proto = request.META.get('SERVER_PROTOCOL', 'http')
            if 'HTTPS' in proto:
                proto = 'https'
            else:
                proto = 'http'
            host = "%s://%s/" % (proto, request.META.get('SERVER_NAME', 'invalid'))
            form.fields["username"].label = host

        return render_to_response(self.get_template(step), dict(context,
            step_field=self.step_field_name,
            step0=step,
            step=step + 1,
            step_count=self.num_steps(),
            form=form,
            previous_fields=previous_fields
        ), context_instance=RequestContext(request))

class LoginForm(forms.Form):
    """Give a login form
    """
    email = forms.CharField(label=_('Email or Username'), initial=_('Your Email'))
    pw = forms.CharField(label=_('Password'), max_length=30, widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get('email', '')
        pw = self.cleaned_data.get('pw', '')
        if email and pw:
            try :
                user = authenticate(username=email, password=pw)
            except User.DoesNotExist :
                raise forms.ValidationError(_("Email or password incorrect"))
            if user:
                if not user.is_active:
                    raise forms.ValidationError(_("This user is not active"))
                return self.cleaned_data
        raise forms.ValidationError(_("Email or password incorrect"))

class NewIdForm(forms.Form):
    """Basic form to add an indentity
    """
    newid = forms.SlugField(label=_('UserID'), max_length=30)

    def clean(self):
        newid = self.cleaned_data.get('newid', '')
        try :
            ident = Identity.objects.get(userid=newid)
        except Identity.DoesNotExist:
            return self.cleaned_data
        raise forms.ValidationError(_("This UserID already exists."))

class IdentityForm(forms.ModelForm):
    """Give a form to create Identity
    """
    class Meta:
        model = Identity
        exclude = ('userprofile', 'userid', 'is_active')

IdentityFormSet = forms.models.modelformset_factory(Identity)

class IdentityPermsForm(forms.ModelForm):
    """Give a form to create Identity
    """
    class Meta:
        model = IdentityPerms
        exclude = ('identity')

IdentityPermsFormSet = forms.models.modelformset_factory(IdentityPerms)

class EmailForm(forms.Form):
    """Form to change Email

    # Good
    >>> data = {'email' : 'a@a.fr', 'email_c' : 'a@a.fr',}
    >>> SubscribeForm(data).is_valid()
    True

    # email differs
    >>> data['email_c'] = 'b@b.fr'
    >>> SubscribeForm(data).is_valid()
    False

    """
    email = forms.EmailField(label=_('Email'), help_text=_('A confirmation mail will be sent to your email address.'))
    email_c = forms.EmailField(label=_('Email confirmation'), help_text=_('Please type again your email address here.'))

    def clean_email(self):
        """Check if email is unique in User and Identity tables
        """
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(_("A user with that email already exists."))

    def clean_email_c(self):
        """Check if email confirmation field is same than email field
        """
        email = self.cleaned_data.get("email", "")
        email_c = self.cleaned_data["email_c"]

        if not email == email_c:
            raise forms.ValidationError(_("The two email fields didnt corresponds."))
        return email_c


class PaswForm(forms.Form):
    """Form to change passwd

    Check somes values like confirmation fields, on uniques fields in tables.

    # Good
    >>> data = {'pw1' : 'toto', 'pw2' : 'toto'}
    >>> SubscribeForm(data).is_valid()
    True

    # password differs
    >>> data['pw2'] = 'truc'
    >>> SubscribeForm(data).is_valid()
    False

    """
    pw1 = forms.CharField(label=_('Password'), help_text=_('Your password.'), widget=forms.PasswordInput)
    pw2 = forms.CharField(label=_('Password confirmation'), help_text=_('Please type again your password.'), widget=forms.PasswordInput)

    def clean_pw2(self):
        """Check if email confirmation field is same than email field
        """
        pw1 = self.cleaned_data.get("pw1", "")
        pw2 = self.cleaned_data["pw2"]

        if not pw1 == pw2:
            raise forms.ValidationError(_("The two password fields didnt corresponds."))
        return pw2
        
class NotifForm(forms.Form):
    """Form to change OpenID notification

    """
    notification_id = forms.EmailField(label=_('Jabber ID'), help_text=_('Enter your Jabber ID'))
    
    def clean_notification_id(self):
        """Check if jid is not mine!
        """
        notification_id = self.cleaned_data["notification_id"]
        if(notification_id == JABBER_ID):
            raise forms.ValidationError(_("This Jabber ID isn't valid !"))
        else:
            return notification_id

class OAuthForm(forms.Form):
    """
    """
    notification_oauth_enabled = forms.BooleanField(label=_('Enable OAuth notification'), required=False)

class IdentityPortraitForm(forms.ModelForm):
    """Give a form to create Identity
    """
    class Meta:
        model = IdentityPortrait
        fields = ["image",]

########################################################################################
# Recaptcha

# http://lobstertech.com/2008/aug/27/integrating_django_recaptcha/

from account.recaptcha.client import captcha
from django.conf import settings
from django.utils.safestring import mark_safe

class ReCaptcha(forms.Widget):
    input_type = None # Subclasses must define this.

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        html = u"<script>var RecaptchaOptions = {theme : '%s'};</script>" % (
            final_attrs.get('theme', 'white'))
        html += captcha.displayhtml(settings.RECAPTCHA_PUBLIC)
        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        return {
            'recaptcha_challenge_field': data.get('recaptcha_challenge_field',
None),
            'recaptcha_response_field': data.get('recaptcha_response_field',
None),
        }

# hack: Inherit from FileField so a hack in Django passes us the
# initial value for our field, which should be set to the IP
class ReCaptchaField(forms.FileField):
    widget = ReCaptcha
    default_error_messages = {
        'invalid-site-public-key': _("Invalid public key"),
        'invalid-site-private-key': _("Invalid private key"),
        'invalid-request-cookie': _("Invalid cookie"),
        'incorrect-captcha-sol': _("Invalid entry, please try again."),
        'verify-params-incorrect': _("The parameters to verify were incorrect, make sure you are passing all the required parameters."),
        'invalid-referrer': _("Invalid referrer domain"),
        'recaptcha-not-reachable': _("Could not contact reCAPTCHA server"),
    }

    def clean(self, data, initial):
        if initial is None or initial == '':
            raise Exception("ReCaptchaField requires the client's IP be set to the initial value")
        ip = initial

        resp = captcha.submit(data.get("recaptcha_challenge_field", None),
                              data.get("recaptcha_response_field", None),
                              settings.RECAPTCHA_PRIVATE, ip)
        if not resp.is_valid:
            raise forms.ValidationError(self.default_error_messages.get(
                    resp.error_code, "Unknown error: %s" % (resp.error_code)))

class CaptchaForm(forms.Form):
    captcha = ReCaptchaField()


