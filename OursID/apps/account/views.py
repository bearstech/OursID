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
# Create your views here.
import xmpp

from django.http import Http404

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from account.forms import *
from models import TrustedConsumers
from django.contrib.auth import logout, login

from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, InvalidPage, EmptyPage
import simplejson as json

# server imports
from server.util import getViewURL
from settings import JABBER_ID, JABBER_PWD

# Error codes:
# login_json(request)
LOGIN_JSON_ERROR_INVALID_PROFILE = 3
LOGIN_JSON_ERROR_INACTIVE_USER = 4
LOGIN_JSON_ERROR_INVALID_LOGIN = 5
LOGIN_JSON_ERROR_INVALID_FORM = 6
LOGIN_JSON_ERROR_INVALID_METHOD = 7

def idPage(request):
    """HomePage :
    If authenticated : redirect to account page
    Else : subscribe form
    """
    if request.user:
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse("accountdetail"))
    form = SubscribeWizard([SubscribeForm, UsernameForm]).get_form(0)
    return render_to_response('account/home.html', {'server_url': getViewURL(request, 'endpoint'),
        'server_xrds_url': getViewURL(request, "idpXrds"), 'form' : form},
        context_instance=RequestContext(request))

def create(request):
    """Show subscription form
    """
    result = {}
    if request.user.is_authenticated():
        result['error'] = _("You already have an account.")
        return render_to_response('account/error.html', result, context_instance=RequestContext(request))
    return render_to_response('account/register_ok.html', result, context_instance=RequestContext(request))

def login_form(request):
    """Show a login form
    """
    result = {}
    if request.user.is_authenticated():
        result['error'] = _("You already are logged.")
        return render_to_response('account/error.html', result, context_instance=RequestContext(request))
    if request.method == "POST":
        result['next'] = request.POST.get('next', reverse('accountdetail'))
        form = LoginForm(request.POST)
        if form.is_valid():
            credentials = form.cleaned_data
            user = authenticate(username=credentials['email'], password=credentials['pw'])
            login(request, user)
            return HttpResponseRedirect(result['next']) # Redirect after POST
        result['form'] = form
        return render_to_response('account/login.html', result, context_instance=RequestContext(request))
    result['next'] = request.GET.get('next', reverse('accountdetail'))
    result['form'] = LoginForm()
    return render_to_response('account/login.html', result, context_instance=RequestContext(request))

@csrf_exempt
def login_json(request):
    """ Perform login in JSON
    """
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            credentials = form.cleaned_data
            user = authenticate(username=credentials['email'], password=credentials['pw'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    try:
                        profile = UserProfile.objects.get(user=request.user, user__is_active=True)
                        if(profile.notification_type == UserProfile.C2DM_NOTIFICATION_TYPE):#TODO registration_id could come from another device. We should check that...
                            response = {"status": profile.notification_state}
                        else:
                            response = {"status": UserProfile.NOT_REGISTERED_NOTIFICATION_STATE}
                    except UserProfile.DoesNotExist:
                        response = {"status": LOGIN_JSON_ERROR_INVALID_PROFILE, "message": "invalid user profile"}
                else:
                    response = {"status": LOGIN_JSON_ERROR_INACTIVE_USER,"message": "inactive user"}
            else:
                response = {"status": LOGIN_JSON_ERROR_INVALID_LOGIN, "message": "invalid login"}
        else:
            response = {"status": LOGIN_JSON_ERROR_INVALID_FORM, "message": "invalid form"}
    else:
        response = {"status": LOGIN_JSON_ERROR_INVALID_METHOD, "message": "invalid method"}
    return HttpResponse(json.dumps(response), mimetype="application/json")

@login_required
def logout_form(request):
    """Logout user
    """
    logout(request)
    #return render_to_response('account/logout.html', result, context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('home')) # Redirect

@login_required
def ident_list(request):
    """
    """
    result = {}
    result['idents'] = Identity.objects.filter(userprofile__user=request.user,
                                               is_active=True)
    return render_to_response('account/identities/list.html', result, context_instance=RequestContext(request))

def ident_show(request, userid, direct=False):
    """Show identity
    """
    result = {}
    # Try to get object, and propose to create if
    # not annonymous else 404
    try:
        ident = Identity.objects.get(userid=userid)
    except Identity.DoesNotExist:
        if request.user.is_authenticated() and not direct:
            result['userid'] = userid
            return render_to_response('account/identities/blank.html', result, context_instance=RequestContext(request))
        else:
            raise Http404

    if not ident.is_active:
        raise Http404

    if direct:
        result['server_url'] = getViewURL(request, 'endpoint')
    result['ident'] = ident
    result['identperms'] = IdentityPerms.objects.get(identity=ident)
    result['useridurl'] = getViewURL(request, 'ident', kwargs={'userid':userid})

    if ident.userprofile.user == request.user:
        result['mine'] = True
        result['assocs'] = TrustedConsumers.objects.filter(identity=ident, user=request.user, always=True)
    return render_to_response('account/identities/show.html', result, context_instance=RequestContext(request))

@login_required
def ident_edit(request, userid):
    """Give a form to modify the identity
    """
    result = {}
    result['userid'] = userid
    try :
        ident = Identity.objects.get(userid=userid, is_active=True)
    except Identity.DoesNotExist:
        result['error'] = 'dontexist'
        return render_to_response('account/identities/modify.html', result, context_instance=RequestContext(request))
    if ident.userprofile.user != request.user:
        result['error'] = 'notmine'
        return render_to_response('account/identities/modify.html', result, context_instance=RequestContext(request))
    result['avaform'] = checkavatarform(request, userid)
    if request.method == 'POST':
        old_id = Identity.objects.get(userid=userid)
        old_idp = IdentityPerms.objects.get(identity=old_id)
        idform = IdentityForm(request.POST, instance=old_id)
        idpform = IdentityPermsForm(request.POST, instance=old_idp)
        if idform.is_valid() and idpform.is_valid:
            ident = idform.save(commit=False)
            ident.userprofile = old_id.userprofile
            ident.userid = userid
            ident.is_active = True
            ident.save()
            identp = idpform.save(commit=False)
            identp.identity = ident
            identp.save()
            return HttpResponseRedirect(reverse('identshow', kwargs={'userid': userid})) # Redirect after POST
        result['idform'] = idform
        result['idpform'] = idpform
        return render_to_response('account/identities/modify.html', result, context_instance=RequestContext(request))
    result['identity'] = ident
    result['idform'] = IdentityForm(instance=ident)
    result['idpform'] = IdentityPermsForm(instance=IdentityPerms.objects.get(identity=ident))
    return render_to_response('account/identities/modify.html', result, context_instance=RequestContext(request))

@login_required
def ident_create(request, userid):
    """Show creation form if identity don't exist
    """
    result = {}
    try :
        ident = Identity.objects.get(userid=userid)
    except Identity.DoesNotExist:
        if request.method == 'POST':
            idform = IdentityForm(request.POST)
            idpform = IdentityPermsForm(request.POST)
            if idform.is_valid() and idpform.is_valid:
                ident = idform.save(commit=False)
                ident.userprofile = request.user.get_profile()
                ident.userid = userid
                ident.is_active = True
                ident.save()
                identp = idpform.save(commit=False)
                identp.identity = ident
                identp.save()
                result['avaform'] = checkavatarform(request, userid)
                return HttpResponseRedirect(reverse('identshow', kwargs={'userid': userid})) # Redirect after POST
            result['idform'] = idform
            return render_to_response('account/identities/create.html', result, context_instance=RequestContext(request))
        result['idform'] = IdentityForm({'username':userid})
        result['idpform'] = IdentityPermsForm()
        result['avaform'] = IdentityPortraitForm()
        return render_to_response( 'account/identities/create.html', result, context_instance=RequestContext(request))
    if ident.userprofile.user == request.user:
        result['error'] = 'exist'
    else:
        result['error'] = 'notmine'
    return render_to_response('account/identities/create.html', result, context_instance=RequestContext(request))

@login_required
def ident_delete(request, userid):
    """Delete user identity
    """
    raise Http404
    result = {}
    try :
        ident = Identity.objects.get(userid=userid)
    except Identity.DoesNotExist:
        result['error'] = 'dontexist'
        return render_to_response('account/identities/delete.html', result, context_instance=RequestContext(request))
    
    if ident.userprofile.user != request.user:
        result['error'] = 'notmine'
        return render_to_response('account/identities/delete.html', result, context_instance=RequestContext(request))

    if request.method == 'POST':
        form = DeleteForm(request.POST)
        if form.is_valid():
            ident.delete()
            result['ok'] = True
            return render_to_response('account/identities/delete.html', result, context_instance=RequestContext(request))
        result['form'] = form
        return render_to_response('account/identities/delete.html', result, context_instance=RequestContext(request))
    result['form'] = DeleteForm()
    return render_to_response( 'account/identities/delete.html', result, context_instance=RequestContext(request))

@login_required
def ident_revokeassoc(request, userid):
    """Show creation form if identity don't exist
    """
    result = {}
    try :
        ident = Identity.objects.get(userid=userid)
    except Identity.DoesNotExist:
        raise Http404

    if request.method == 'POST' and request.POST:
        for host in request.POST.keys():
            try :
                assoc = TrustedConsumers.objects.get(user=request.user, identity__userid=userid, host=host)
            except TrustedConsumers.DoesNotExist:
                result['error'] = _('No trusted consumer found.')
                return render_to_response('account/error.html', result, context_instance=RequestContext(request))
            else:
                assoc.delete()
        return HttpResponseRedirect(reverse('identshow', kwargs={'userid': userid})) # Redirect after POST
    raise Http404

@login_required
def details(request):
    """Dashboard for user.
    """
    result = {}
    result['idents'] = Identity.objects.filter(userprofile__user=request.user,
                                               is_active=True)

    if request.method == 'POST':
        newidform = NewIdForm(request.POST)
        if newidform.is_valid():
            newid = newidform.cleaned_data['newid']
            return HttpResponseRedirect(reverse('identcreate', kwargs={'userid': newid})) # Redirect after POST
        else:
            result['newidform'] = newidform
    else:
        result['newidform'] = NewIdForm()
    return render_to_response('account/dashboard.html', result, context_instance=RequestContext(request))

@login_required
def ident_change(request):
    """Redirections for ident form
    """
    if request.method == "POST":
        if not request.POST.has_key('ident'):
            return HttpResponseRedirect(reverse('accountdetail',)) # Redirect after POST
        ident = request.POST['ident']
        if request.POST.has_key('edit'):
            return HttpResponseRedirect(reverse('identedit', kwargs={'userid': ident})) # Redirect after POST
        elif request.POST.has_key('edit'):
            return HttpResponseRedirect(reverse('identdelete', kwargs={'userid': ident})) # Redirect after POST
    raise Http404

@login_required
def delete(request):
    """
    """
    return render_to_response('dummy.html', context_instance=RequestContext(request))

@login_required
def edit(request):
    """Show informations for customer
    """
    user = request.user
    profile = user.get_profile()
    result = {}
    if(profile.notification_type == UserProfile.JABBER_NOTIFICATION_TYPE):
        if(profile.notification_state == UserProfile.VALID_NOTIFICATION_STATE):
            notification_status = _('Jabber notification enabled on ') + profile.notification_id
        else:
            notification_status = _('Jabber notification disabled')
    elif(profile.notification_type == UserProfile.C2DM_NOTIFICATION_TYPE):
        notification_status = _('Google Android C2DM notification with GrizzlID application')
        result['oauthform'] = OAuthForm({'notification_oauth_enabled': profile.notification_oauth_enabled})
    else:
        notification_status = _('None')


    result['emailform'] = EmailForm()
    result['paswform'] = PaswForm()
    result['notifform'] = NotifForm()
    result['notification_status'] = notification_status
    return render_to_response('account/edit/edit.html', result, context_instance=RequestContext(request))

@login_required
def editnotif(request):
    """To edit OpenID notification settings
       Send jabber subscribe stenza to specified JID
	Checks:
	- submitted form is valid
    """
    result = {}
    if request.method == 'POST':
        notifform = NotifForm(request.POST)
        if notifform.is_valid():
            user = request.user
            profile = user.get_profile()
            profile.notification_type = UserProfile.JABBER_NOTIFICATION_TYPE
            profile.notification_id = notifform.cleaned_data['notification_id']
            profile.notification_state = UserProfile.VALID_NOTIFICATION_STATE
            profile.save()
            # jabber subscribe stenza
            jid=xmpp.protocol.JID(JABBER_ID)
            dst = xmpp.protocol.JID(profile.notification_id)
            cl=xmpp.Client(jid.getDomain(),debug=[])
            if cl.connect() == "":
                result['form'] = notifform
                return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))
            if cl.auth(jid.getNode(),JABBER_PWD) == None:
                result['form'] = notifform
                return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))
            msg = _('Hi from GrizzlID ! If you would like to receive OpenID authentification requests on this Jabber account, accept me.')
            cl.send(xmpp.protocol.Presence(dst.getStripped(),'subscribe', None, None, msg))
            cl.disconnect()
            return HttpResponseRedirect(reverse('accounteditnotifok')) # Redirect after POST
        result['form'] = notifform
        return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))
    result['form'] = NotifForm()
    return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))

def editnotifok(request):
    """Send message to user: notification change is ok
    """
    message = _('Your notification configuration was successfully changed. A subscription request has been sent to your Jabber ID!')
    result = {'message': message}
    result['title'] = "OK !"
    return render_to_response('account/message.html',result, context_instance=RequestContext(request))

@login_required
def editoauth(request):
    """
    """
    result = {}
    if request.method == 'POST':
        oauthform = OAuthForm(request.POST)
        if oauthform.is_valid():
            user = request.user
            profile = user.get_profile()
            profile.notification_oauth_enabled = oauthform.cleaned_data['notification_oauth_enabled']
            profile.save()
            return HttpResponseRedirect(reverse('accounteditoauthok')) # Redirect after POST
        result['form'] = oauthform
        return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))
    result['form'] = OAuthForm()
    return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))

def editoauthok(request):
    """Send message to user: oauth notification change is ok
    """
    message = _('Your notification configuration was successfully changed.')
    result = {'message': message}
    result['title'] = "OK !"
    return render_to_response('account/message.html',result, context_instance=RequestContext(request))

@login_required
def editpasw(request):
    """Simple form to edit passwd
    """
    result = {}
    if request.method == 'POST':
        paswform = PaswForm(request.POST)
        if paswform.is_valid():
            user = request.user
            user.set_password(paswform.cleaned_data['pw1'])
            user.save()
            return HttpResponseRedirect(reverse('accounteditpaswok')) # Redirect after POST
        result['form'] = paswform
        return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))
    result['form'] = PaswForm()
    return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))

@login_required
def editpaswok(request):
    """Send message to user : password change is ok
    """
    message = _('Your password was successfully changed.')
    result = {'message': message}
    result['title'] = "OK !"
    return render_to_response('account/message.html',result, context_instance=RequestContext(request))

@login_required
def editemail(request):
    """
    """
    result = {}
    if request.method == 'POST':
        emailform = EmailForm(request.POST)
        if emailform.is_valid():
            user = request.user
            user.email = emailform.cleaned_data['email']
            user.is_active = False
            user.save()
            profile = user.get_profile()
            profile.generateconfirmcode()
            profile.save()
            profile.sendemail(request)
            return HttpResponseRedirect(reverse('accounteditemailok')) # Redirect after POST
        result['form'] = emailform
        return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))
    result['form'] = EmailForm()
    return render_to_response('account/edit/form.html', result, context_instance=RequestContext(request))

def editemailok(request):
    """Send message : email change is ok
    """
    message = _('Your email was succesfuly changed and you are loggued out, please read the confirmation email.')
    result = {'message': message}
    result['title'] = "OK !"
    return render_to_response('account/message.html',result, context_instance=RequestContext(request))

@login_required
def history(request, page=1):
    """Show all RP for a user
    """
    result = {}
    from account.models import RPHistory
    history = RPHistory.objects.filter(identity__userprofile__user=request.user)

    if len(history) != 0:
        # Paginate it
        paginator = Paginator(history, 10)

        # If page request (9999) is out of range, deliver last page of results.
        try:
            history_p = paginator.page(page)
        except (EmptyPage, InvalidPage):
            return HttpResponseRedirect(reverse('accounthistorypage', (), {'page': paginator.num_pages})) # Redirect after POST

        result['history'] = history_p

    return render_to_response('account/history.html', result, context_instance=RequestContext(request))


def checkavatarform(request, userid):
    """Checks if a avatar form is filled, create avatar if needed
    """
    if request.method == 'POST':
        try :
            idp = IdentityPortrait.objects.get(identity__userid=userid)
        except IdentityPortrait.DoesNotExist:
            idp = IdentityPortrait(identity=Identity.objects.get(userid=userid))
        idpform = IdentityPortraitForm(request.POST,request.FILES, instance=idp)
        if idpform.is_valid():
            return idpform.save()
    return IdentityPortraitForm()

def confirm(request, code):
    """Check a confirmation code and activate user.
    """
    result = {}
    try :
        profile = UserProfile.objects.get(confirmcode=code, user__is_active=False)
    except UserProfile.DoesNotExist:
        result['error'] = True
        return render_to_response('account/confirm.html', result, context_instance=RequestContext(request))
    profile.confirm()
    profile.user.backend = 'django.contrib.auth.backends.ModelBackend'
    login(request, profile.user)
    return render_to_response('account/confirm.html', result, context_instance=RequestContext(request))


