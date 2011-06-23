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
import datetime
import simplejson as json

from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from account.models import UserProfile
from oauth_forwarder.models import OAuthRequest
from oauth_forwarder.forms import *
from c2dm_notifier.utils import *

def index(request):
    result = {'current_host': request.get_host()}
    return render_to_response('oauth_forwarder/index.html',result, context_instance=RequestContext(request))

@csrf_exempt
def finalize(request):
    response = {}
    try :
        oauth_url = request.POST['oauth_url']
        oauth_callback = request.POST['oauth_callback']
        oauth_request = OAuthRequest.objects.filter(oauth_url=oauth_url).latest('date_created')
        oauth_request.oauth_callback = oauth_callback
        oauth_request.validation = OAuthRequest.VALIDATION_ACCEPTED
        oauth_request.save()
        response = {'status': 'ok'}
    except OAuthRequest.DoesNotExist:
        response = {'status': 'failed', 'message': 'Unknown OAuth request !'}
    except KeyError:
        response = {'status': 'failed', 'message': 'Post param missing !'}
    return HttpResponse(json.dumps(response), mimetype="application/json")

def forward(request):
    result = {}
    if 'url' not in request.GET:
        return HttpResponseRedirect(reverse('oauth_forwarder:index'))

    oauth_url = request.GET['url']
    validate = URLValidator(verify_exists=False)
    try:
        validate(oauth_url)
    except ValidationError:
        result['error'] = _('Error: invalid URL !')
        return render_to_response('oauth_forwarder/error.html', result, context_instance=RequestContext(request))

    result['oauth_url'] = oauth_url
    if request.method != 'POST':
        result['emailform'] = EmailForm()
        return render_to_response('oauth_forwarder/forward.html', result, context_instance=RequestContext(request))

    emailform = EmailForm(request.POST)
    result['emailform'] = emailform
    if not emailform.is_valid():
        return render_to_response('oauth_forwarder/forward.html', result, context_instance=RequestContext(request))

    try:
        user_profile = UserProfile.objects.get(user__email=emailform.cleaned_data['email'])
    except UserProfile.DoesNotExist:
        messages.add_message(request, messages.ERROR, _('Unknown user profile!'))
        return render_to_response('oauth_forwarder/forward.html', result, context_instance=RequestContext(request))

    if user_profile.notification_oauth_enabled != True:
        messages.add_message(request, messages.ERROR, _('OAuth notification is disabled! Please enable OAuth notification in your account settings.'))
        return render_to_response('oauth_forwarder/forward.html', result, context_instance=RequestContext(request))

    if user_profile.notification_state != UserProfile.VALID_NOTIFICATION_STATE or user_profile.notification_type != UserProfile.C2DM_NOTIFICATION_TYPE:
        messages.add_message(request, messages.ERROR, _('No notification device set!'))
        return render_to_response('oauth_forwarder/forward.html', result, context_instance=RequestContext(request))

    oauthrequest = OAuthRequest(oauth_url=oauth_url, date_created=datetime.datetime.now(), userprofile=user_profile)
    oauthrequest.save()
    values = {
                'registration_id': user_profile.notification_id,
                'collapse_key': '2',
                'data.id': oauthrequest.id,
                'data.type': 'oauth',
                'data.oauth_url': oauthrequest.oauth_url,
            }
    notif_result = send_c2dm_message(values, True)
    if notif_result == UserProfile.VALID_NOTIFICATION_STATE:
        result['message'] = _('OAuth request has been forwarded to your device. This page will be automatically refreshed as soon as you answer.')
    elif notif_result == UserProfile.NOT_REGISTERED_NOTIFICATION_STATE:
        result['message'] = _('Error: your device is not registered!')
    elif notif_result == UserProfile.INVALID_REGISTRATION_NOTIFICATION_STATE:
        result['message'] = _('Error: invalid device registration!')
    else:
        result['message'] = _("Ooups... There's an error (%i)! We've been notified and we'll try to solve it as soon as possible.") % notif_result
    return render_to_response('oauth_forwarder/wait.html',result, context_instance=RequestContext(request))

def status(request):
    response = {}
    if 'url' in request.GET:
        oauth_url = request.GET['url']
        try:
            oauth_request = OAuthRequest.objects.filter(oauth_url=oauth_url).latest('date_created')
            if oauth_request.validation == OAuthRequest.VALIDATION_ACCEPTED:
                response = {'status': 'ok', 'oauth_callback': oauth_request.oauth_callback}
            elif oauth_request.validation == OAuthRequest.VALIDATION_REFUSED:
                response = {'status': 'refused'}
            else:
                response = {'status': 'pending'}
        except OAuthRequest.DoesNotExist:
            # Return an error response
            response = {"status": "failed", "message": "Couldn't retrieve OAuth request!"}
    else:
        response = {"status": "failed", "message": "URL parameter missing!"}
    return HttpResponse(json.dumps(response), mimetype="application/json")
