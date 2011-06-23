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
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

import util, datetime, pickle, settings, xmpp
from urlparse import urlparse
#
from django import http
from django.views.generic.simple import direct_to_template
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render_to_response
#
from openid.server.server import Server, ProtocolError, CheckIDRequest, \
     EncodingError
from openid.server.trustroot import verifyReturnTo
from openid.yadis.discover import DiscoveryFailure
from openid.consumer.discover import OPENID_IDP_2_0_TYPE
from openid.extensions import sreg
from openid.fetchers import HTTPFetchingError
from django.core.urlresolvers import reverse
from account.models import Identity, TrustedConsumers, UserProfile
from server.models import OidRequest
from c2dm_notifier.utils import *
from django.http import HttpResponseRedirect
from django.http import HttpResponse
import simplejson as json

from settings import JABBER_ID, JABBER_PWD

OIDREQUEST_STORAGE_SESSION = 1
OIDREQUEST_STORAGE_DATABASE = 2

# Error codes:
# registerC2DM(registration_id)
C2DM_REGISTRATION_SUCCEED = 0
C2DM_REGISTRATION_ERROR_NOT_LOGGED = 1
C2DM_REGISTRATION_ERROR_BAD_PROFILE = 2
# oidrequest(oidrequest_id, action)
OIDREQUEST_SUCCEED = 0
OIDREQUEST_ERROR_BAD_IDENTITY = 1
OIDREQUEST_ERROR_BAD_REQUEST = 2
OIDREQUEST_ERROR_BAD_SESSION = 3
OIDREQUEST_ERROR_BAD_ACTION = 4
#sendNotification(oidrequest)
CONNECTION_XMPP_ERROR = 13
AUTH_XMPP_ERROR = 14

def server(request):
    """Respond to requests for the server's primary web page.
    """
    return direct_to_template(
        request,
        'server/index.html',
        {'user_url': reverse("idpage"),
         'server_xrds_url': util.getViewURL(request, "idpXrds"),
         },context_instance=RequestContext(request))

def idpXrds(request):
    """Respond to requests for the IDP's XRDS document, which is used in
    IDP-driven identifier selection.
    """
    return util.renderXRDS(
        request, [OPENID_IDP_2_0_TYPE], [util.getViewURL(request, "endpoint")])

@csrf_exempt
def endpoint(request):
    """Respond to low-level OpenID protocol messages.
    """
    s = util.getServer(request)
    query = util.normalDict(request.GET or request.POST)

    # First, decode the incoming request into something the OpenID
    # library can use.
    try:
        openid_request = s.decodeRequest(query)
    except ProtocolError, why:
        # This means the incoming request was invalid.
        return direct_to_template(
            request,
            'server/endpoint.html',
            {'error': str(why)})

    # If we did not get a request, display text indicating that this
    # is an endpoint.
    if openid_request is None:
        # Hook for continue auth after a login redirect
        handle = request.session.get("handle", False)
        if handle:
            if handle == OIDREQUEST_STORAGE_SESSION:
                openid_request = request.session['oidrequest']
                del request.session['oidrequest']
                del request.session['handle']
            else:
                try:
                    oidrequest = OidRequest.objects.get(id=request.session['oidrequest'])
                    openid_request = pickle.loads(str(oidrequest.openid_request))
                    oidrequest.delete()
                except OidRequest.DoesNotExist:
                    return direct_to_template(request, 'server/endpoint.html',
                           {'error': "Couldn't retrieve identity!(%i)" % (OIDREQUEST_STORAGE_DATABASE,)})
                finally:
                    del request.session['oidrequest']
                    del request.session['handle']
            return handleCheckIDRequest(request, openid_request)
        else:
            return direct_to_template(
                request,
                'server/endpoint.html',
                {})

    # We got a request; if the mode is checkid_*, we will handle it by
    # getting feedback from the user or by checking the session.
    if openid_request.mode in ["checkid_immediate", "checkid_setup"]:
        if not request.user.is_authenticated():
            identity = checkRemoteNotification(openid_request)
            if identity and openid_request.mode == "checkid_setup":
                sreg_req = sreg.SRegRequest.fromOpenIDRequest(openid_request)
                required_fields = json.dumps(sreg_req.required)
                oidrequest = OidRequest(openid_request=pickle.dumps(openid_request), date_created=datetime.datetime.now(), identity=identity, required_fields=required_fields, trust_root=openid_request.trust_root)
                oidrequest.save()
                request.session['oidrequest'] = oidrequest.id
                request.session['handle'] = OIDREQUEST_STORAGE_DATABASE
                notif_ret = sendNotification(oidrequest)
                if notif_ret == UserProfile.VALID_NOTIFICATION_STATE:
                    messages.info(request, _('A notification has been sent to your device !'))
                else:
                    messages.error(request, _('Error %i : couldn\'t notify your device!') % notif_ret)
            else:
                request.session['oidrequest'] = openid_request
                request.session['handle'] = OIDREQUEST_STORAGE_SESSION
        return handleCheckIDRequest(request, openid_request)
    else:
        # We got some other kind of OpenID request, so we let the
        # server handle this.
        openid_response = s.handleRequest(openid_request)
        return displayResponse(request, openid_response)

def checkRemoteNotification(openid_request):
    """ Check if this openid_request could be notified to an user
    Checks :
     - Existing userid is requested by consumer
     - This userid is an user's userid
     - This user has a notification device configured ?
    Returns Identity if succeed, else returns False
    """
    # Parse IDP (http://domain.tld/ident <- ident)
    userid = urlparse(openid_request.identity)[2].strip('/')
    if len(userid) != 0:
        try:
            identity = Identity.objects.get(userid=userid, is_active=True)
            if ((identity.userprofile.notification_type != UserProfile.NONE_NOTIFICATION_TYPE) and (identity.userprofile.notification_state == UserProfile.VALID_NOTIFICATION_STATE)):
                return identity
            else:
                return False
        except Identity.DoesNotExist:
            return False
    else:
        return False

def oidrequest(request, oidrequest_id, action):
    """Handle actions about OidRequests
    Checks :
     - User really owns requested OidRequest identified by oidrequest_id
     Returns JSON message
    """
    response = {}
    if request.user and request.user.is_authenticated():
        if len(oidrequest_id) > 0:
            try:
                oidrequest = OidRequest.objects.get(id=oidrequest_id)
                openid_request = pickle.loads(str(oidrequest.openid_request))
                identity = Identity.objects.get(userprofile__user=request.user, userid=oidrequest.identity.userid,is_active=True)
                if (action == 'accept'):
                    oidrequest.validation = OidRequest.VALIDATION_ACCEPTED
                    oidrequest.save()
                    response = {"status": OIDREQUEST_SUCCEED}
                elif (action == 'refuse'):
                    oidrequest.validation = OidRequest.VALIDATION_REFUSED
                    oidrequest.save()
                    response = {"status": OIDREQUEST_SUCCEED}
                else:
                    response = {"status": OIDREQUEST_ERROR_BAD_ACTION, "message": "Unknown action !"}
            except OidRequest.DoesNotExist:
                # Return an error response
                response = {"status": OIDREQUEST_ERROR_BAD_REQUEST, "message": "Couldn't retrieve OpenID request!"}
            except Identity.DoesNotExist:
                # Hey ! User try to stolen other identity...
                response = {"status": OIDREQUEST_ERROR_BAD_IDENTITY, "message": "This is not your identity!"}
        else:
            requests = []
            oidrequests = OidRequest.objects.filter(identity__userid=request.user).order_by('-date_created')[:20]
            for oidrequest in oidrequests:
                request_id = oidrequest.id
                trust_root = oidrequest.trust_root
                identity = oidrequest.identity.userid
                date_created = str(oidrequest.date_created)
                validation = oidrequest.validation
                required_fields = json.loads(oidrequest.required_fields)
                requests.append({'id': request_id, 'trust_root': trust_root,'identity': identity, 'date_created': date_created, 'validation': validation, 'required_fields': required_fields})
            response = {"status": OIDREQUEST_SUCCEED, "data": requests}
    else:
        response = {"status": OIDREQUEST_ERROR_BAD_SESSION, "message": "Not logged in!"}
    return HttpResponse(json.dumps(response), mimetype="application/json")

@login_required
def handleCheckIDRequest(request, openid_request):
    """Handle checkid_* requests.
    Checks :
     - Existing userid is requested by consumer
     - This userid is an user's userid
     - Does user allow direct auth?
     - Is it an direct-access auth?

    """
    direct_auth = False
    userid = ''

    # Consumer can send an idselect request to let
    # user choose his identity in server.
    # But if it no do it, we use provided identity.
    if not openid_request.idSelect():
        # Get homepage full uri
        home_url = util.getViewURL(request, 'home')

        # Parse IDP (http://domain.tld/ident <- ident)
        from urlparse import urlparse
        userid = urlparse(openid_request.identity)[2].strip('/')

        # If isn't user's identity, return error response  !NOTEST!
        try:
            Identity.objects.get(userprofile__user=request.user, userid=userid,
                                is_active=True)
        except Identity.DoesNotExist:
            # Return an error response
            error_response = ProtocolError(
                openid_request.message,
                "%s is not user's identity" %
                (openid_request.identity,))
            return displayResponse(request, error_response)

        if len(userid) != 0:
            # Consumer give to us an userid
            id_url = util.getViewURL(request, 'ident', kwargs={'userid':userid})
            if not openid_request.identity.endswith("/"):
                id_url = id_url.rstrip("/")
        else:
            id_url = ''

        # Confirm that this server can actually vouch for that
        # identifier
        # test :
        #  - homepage for v2 like auth
        #  - identity
        if not openid_request.identity in (home_url, id_url):
            # Return an error response
            error_response = ProtocolError(
                openid_request.message,
                "This server cannot verify the URL %r" %
                (openid_request.identity,))

            return displayResponse(request, error_response)

    # Ok for a Direct auth ?
    # User can accept authentications for an host with an id without
    # confirmation if he trust it
    try :
        if userid:
            trust = TrustedConsumers.objects.get(host=openid_request.trust_root, user=request.user, identity__userid=userid, always=True)
        else:
            trust = TrustedConsumers.objects.get(host=openid_request.trust_root, user=request.user, always=True)
    except TrustedConsumers.DoesNotExist:
        direct_auth = False
    else:
        direct_auth = True
    # Now make a decision

    if direct_auth:
        # If we have direct address and trust association
        # lets allow auth
        ###
        userid = trust.identity.userid
        openid_response = generate_response(request, True, openid_request, userid, send_sreg=False)
        return displayResponse(request, openid_response)

    elif openid_request.immediate and not direct_auth:
        # If we have an direct address but no trust association,
        # cancel auth
        ###
        openid_response = openid_request.answer(False)
        return displayResponse(request, openid_response)

    else:
        # Store the incoming request object in the session so we can
        # get to it later.
        util.setRequest(request, openid_request)
        return showDecidePage(request, openid_request, userid)

def showDecidePage(request, openid_request, userid=''):
    """Render a page to the user so a trust decision can be made.

    @type openid_request: openid.server.server.CheckIDRequest
    """
    result = formatOidRequest(request, openid_request, userid)
    return direct_to_template(
        request, 'server/trust.html',
        result, context_instance=RequestContext(request))

def unregisterNotification(user_profile):
    user_profile.notification_type = UserProfile.NONE_NOTIFICATION_TYPE
    user_profile.notification_id = ''
    user_profile.notification_state = UserProfile.NOT_REGISTERED_NOTIFICATION_STATE
    user_profile.save()

def formatOidRequest(request, openid_request, userid=''):
    result = {}
    err = None
    trust_root = openid_request.trust_root
    return_to = openid_request.return_to

    # Get requested fields
    requested = sreg.SRegRequest.fromOpenIDRequest(openid_request).allRequestedFields()

    try:
        # Stringify because template's ifequal can only compare to strings.
        trust_root_valid = verifyReturnTo(trust_root, return_to) \
                           and "Valid" or "Invalid"
    except DiscoveryFailure, err:
        trust_root_valid = "DISCOVERY_FAILED"
    except HTTPFetchingError, err:
        trust_root_valid = "Unreachable"

    # If an userid is provided only use this identity, else fetch all user's
    # identity
    if not userid:
        identities = Identity.objects.filter(userprofile__user=request.user,
                                             is_active=True)
    else:
        identities = Identity.objects.filter(userprofile__user=request.user,
                                             userid=userid, is_active=True)
        # Try to find default identity for this host
        try:
            assoc = TrustedConsumers.objects.get(host=openid_request.trust_root, user=request.user, always=True)
        except TrustedConsumers.DoesNotExist :
            pass
        else:
            result['defaultid'] = assoc.identity

    result['trust_root'] = trust_root
    result['return_to'] = return_to
    result['identities'] = identities
    result['requested'] = requested
    result['trust_handler_url'] = reverse("prslt")
    result['trust_root_valid'] = trust_root_valid
    result['err'] = err
    return result

def oidRequestStatus(request):
    """ Return status of last OpenID request notification
	Returns a JSON message
    """
    response = {}
    handle = request.session.get("handle", False)
    if handle == OIDREQUEST_STORAGE_DATABASE:
        try:
            oidrequest = OidRequest.objects.get(id=request.session['oidrequest'])
            openid_request = pickle.loads(str(oidrequest.openid_request))
            if oidrequest.validation != OidRequest.VALIDATION_PENDING:
                response = {'status': 'ok'}
            else:
                response = {'status': 'pending'}
        except OidRequest.DoesNotExist:
            # Return an error response
            response = {"status": "failed", "message": "Couldn't retrieve OpenID request!"}
    else:
        response = {"status": "failed", 'message': 'no oidrequest'}
    return HttpResponse(json.dumps(response), mimetype="application/json")

def processRemoteTrustResult(request):
    """ Process a validated OpenID request.
    Called by UserAgent.
    Checks:
    - client has an oidrequest stored in database (identified in his session)
    - oidrequest has been validated (accepted or refused)
    Returns an openid response, or an error page.
    """
    handle = request.session.get("handle", False)
    if handle == OIDREQUEST_STORAGE_DATABASE:
        try:
            oidrequest = OidRequest.objects.get(id=request.session['oidrequest'])
            openid_request = pickle.loads(str(oidrequest.openid_request))
            if oidrequest.validation != OidRequest.VALIDATION_PENDING:
                # Choose identity to answer with
                userid = oidrequest.identity

                # If the decision was to allow the verification, respond
                # accordingly.
                allowed = (oidrequest.validation == OidRequest.VALIDATION_ACCEPTED or oidrequest.validation == OidRequest.VALIDATION_ALWAYS_ACCEPTED)

                # Does we always trust this consumer for this identity?
                alwaystrust = (oidrequest.validation == OidRequest.VALIDATION_ALWAYS_ACCEPTED)

                openid_response = generate_response(request, allowed, openid_request, userid, alwaystrust)
                oidrequest.delete()
                return displayResponse(request, openid_response)
            else:
                return direct_to_template(request, 'server/endpoint.html',
                           {'error': "OidRequest not validated!(%i)" % (oidrequest.validation,)})
        except OidRequest.DoesNotExist:
            return direct_to_template(request, 'server/endpoint.html',
                   {'error': "Couldn't retrieve identity!(%i)" % (OIDREQUEST_STORAGE_DATABASE,)})
        finally:
            del request.session['oidrequest']
            del request.session['handle']
    else:
        return direct_to_template(request, 'server/endpoint.html',
                   {'error': "Couldn't handle this openid request(%i)" % (handle,)})

@login_required
def processTrustResult(request):
    """
    Handle the result of a trust decision and respond to the RP
    accordingly.
    """
    # Get the request from the session so we can construct the
    # appropriate response.
    openid_request = util.getRequest(request)

    # Respond with correct identity
    id = openid_request.identity
    home_url = util.getViewURL(request, "home")

    # If the decision was to allow the verification, respond
    # accordingly.
    allowed = 'allow' in request.POST or 'alwaystrust' in request.POST

    # Choose identity to answer with
    #
    # If no identity given by user choose the first
    try :
        userid = request.POST['identity']
    except KeyError:
        if openid_request.idSelect():
            userid = Identity.objects.filter(userprofile__user=request.user,
                                             is_active=True)[0].userid
    else:
        # Does user have this identity?
        try :
            Identity.objects.get(userprofile__user=request.user, userid=userid,
                                is_active=True)
        except Identity.DoesNotExist:
            # Hey ! User try to stolen other identity...
            allowed = False

    # Double check if user give right identity
    if not openid_request.idSelect():
        # Id requested http://domain.tld/userid
        from urlparse import urlparse
        parsed_id = urlparse(id)[2].strip('/')
        if parsed_id != userid:
            # User want to answer with a non requested id
            allowed = False

    # Does we always trust this consumer for this identity?
    alwaystrust = 'alwaystrust' in request.POST and allowed

    openid_response = generate_response(request, allowed, openid_request, userid, alwaystrust)

    return displayResponse(request, openid_response)
    
def registerC2DM(request, registration_id):
    """ Register C2DM notification token (Google) for this user
    Checks :
     - no @login_required; using manual login verification instead of @login_required (avoid redirection in JSON requests)
     - registration_id isn't already registered
    Returns JSON confirmation
    """
    response = {}
    if request.user and request.user.is_authenticated():
        try:
            try:
                prev_profile = UserProfile.objects.get(notification_id=registration_id, notification_type=UserProfile.C2DM_NOTIFICATION_TYPE)
                unregisterNotification(prev_profile)
            except UserProfile.DoesNotExist:
                pass

            profile = UserProfile.objects.get(user=request.user, user__is_active=True)
            profile.notification_type = UserProfile.C2DM_NOTIFICATION_TYPE
            profile.notification_id = registration_id
            profile.notification_state = UserProfile.VALID_NOTIFICATION_STATE
            profile.save()
            response = {'status': C2DM_REGISTRATION_SUCCEED}
        except UserProfile.DoesNotExist:
            # Return an error response
            response = {"status": C2DM_REGISTRATION_ERROR_BAD_PROFILE, "message": "Couldn't retrieve user profile!"}
    else:
        response = {"status": C2DM_REGISTRATION_ERROR_NOT_LOGGED, "message": "Not logged in!"}
    return HttpResponse(json.dumps(response), mimetype="application/json")

def sendNotification(oidrequest):
    user_profile = oidrequest.identity.userprofile
    registration_id = user_profile.notification_id
    notification_type = user_profile.notification_type
    if(notification_type == UserProfile.C2DM_NOTIFICATION_TYPE):
        values = {
                'registration_id': registration_id,
                'collapse_key': '1',
                'data.id': oidrequest.id,
                'data.type': 'openid',
                'data.trust_root': oidrequest.trust_root,
                'data.required_fields': oidrequest.required_fields,
            }
        notif_result = send_c2dm_message(values)

        if notif_result == UserProfile.INVALID_REGISTRATION_NOTIFICATION_STATE or notif_result == UserProfile.NOT_REGISTERED_NOTIFICATION_STATE:
            user_profile.notification_state = notif_result
            user_profile.save()
        return notif_result
    elif (notification_type == UserProfile.JABBER_NOTIFICATION_TYPE):
        src = xmpp.protocol.JID(JABBER_ID)
        dst = xmpp.protocol.JID(registration_id)
        passwd = JABBER_PWD
        cl=xmpp.Client(src.getDomain(),debug=[])
        if cl.connect() == "":
            return CONNECTION_XMPP_ERROR
        if cl.auth(src.getNode(), passwd, src.getResource()) == None:
            return AUTH_XMPP_ERROR
        msg = _('The website %s is requesting access to your GrizzlID identity.') % oidrequest.trust_root
        required_fields = json.loads(oidrequest.required_fields)
        if(len(required_fields) > 0):
            msg += _(' The following personal informations will be shared: %s') % ', '.join(required_fields)
        msg += ' ? (yes|no)'
        cl.send(xmpp.protocol.Message(dst.getStripped(),msg, 'chat'))
        cl.disconnect()
    return UserProfile.VALID_NOTIFICATION_STATE

def generate_response(request, allow, openid_request, userid, alwaystrust=False, send_sreg=True):
    """Generate openid response and history
    """
    # Get identity url
    response_identity = util.getViewURL(request, 'ident', kwargs={'userid' : userid})

    if not openid_request.identity.endswith("/") or openid_request.idSelect():
        response_identity = response_identity.rstrip("/")

    # What is the identity?
    user_id = Identity.objects.get(userid=userid)

    # Generate a response with the appropriate answer.
    openid_response = openid_request.answer(allow,
                                            identity=response_identity)
    if allow:
        if send_sreg:
            # Send Simple Registration data in the response, if appropriate.
            sreg_data = user_id.getsreg()

            # Get requested fields
            sreg_req = sreg.SRegRequest.fromOpenIDRequest(openid_request)

            # fill fields
            sreg_resp = sreg.SRegResponse.extractResponse(sreg_req, sreg_data)
            openid_response.addExtension(sreg_resp)

        # Does we retain this consumer?
        if alwaystrust:
            trust = TrustedConsumers(host=openid_request.trust_root, user=request.user, identity=user_id, always=True)
            trust.save()
    # Save this response
    from account.models import RPHistory
    ip = request.META["REMOTE_ADDR"]
    rphist = RPHistory(identity=user_id, host=openid_request.trust_root, auth_result=allow, ip=ip)
    rphist.save()

    return openid_response

def displayResponse(request, openid_response):
    """Display an OpenID response.  Errors will be displayed directly to
    the user; successful responses and other protocol-level messages
    will be sent using the proper mechanism (i.e., direct response,
    redirection, etc.).
    """
    s = util.getServer(request)

    # Encode the response into something that is renderable.
    try:
        webresponse = s.encodeResponse(openid_response)
    except EncodingError, why:
        # If it couldn't be encoded, display an error.
        text = why.response.encodeToKVForm()
        return direct_to_template(
            request,
            'server/endpoint.html',
            {'error': text}, context_instance=RequestContext(request))

    # Construct the appropriate django framework response.
    r = http.HttpResponse(webresponse.body)
    r.status_code = webresponse.code

    for header, value in webresponse.headers.iteritems():
        r[header] = value
    return r
