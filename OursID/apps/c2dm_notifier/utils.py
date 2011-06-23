#Original code: django-c2dm (https://github.com/scottferg/django-c2dm)
######################################################################
# Copyright (c) 2010, Scott Ferguson
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the software nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY SCOTT FERGUSON ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL SCOTT FERGUSON BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.conf import settings

import urllib, urllib2, datetime, logging
from urllib2 import URLError, HTTPError
from account.models import UserProfile

C2DM_URL = 'https://android.apis.google.com/c2dm/send'
UNKNOWN_ERROR = -1

logger = logging.getLogger('django.request')

def send_c2dm_message(values, delay_while_idle = False):
    '''
    Sends a message to the device.  
    
    delay_while_idle - If included, indicates that the message should not be sent immediately if the device is idle. The server will wait for the device to become active, and then only the last message for each collapse_key value will be sent.
    '''

    if delay_while_idle:
        values['delay_while_idle'] = ''

    headers = {
        'Authorization': 'GoogleLogin auth=%s' % settings.C2DM_AUTH_TOKEN,
    }

    try:
        params = urllib.urlencode(values)
        request = urllib2.Request(C2DM_URL, params, headers)

        # Make the request
        response = urllib2.urlopen(request)

        result = response.read().split('=')

        if 'Error' in result:
            if result[1] == 'InvalidRegistration':
                return UserProfile.INVALID_REGISTRATION_NOTIFICATION_STATE
            elif result[1] == 'NotRegistered':
                return UserProfile.NOT_REGISTERED_NOTIFICATION_STATE
            raise Exception(result[1])
        else:
            return UserProfile.VALID_NOTIFICATION_STATE
    except HTTPError, e:
        logger.error('c2dm_notifier::send_c2dm_message: HTTPError %d' % (e.code,) )
        return e.code
    except URLError, e:
        logger.error('c2dm_notifier::send_c2dm_message: URLError %s' % (str(e.reason),) )
        return UNKNOWN_ERROR
    except Exception, error:
        logger.error('c2dm_notifier::send_c2dm_message: Exception %s' % (str(error),) )
        return UNKNOWN_ERROR
