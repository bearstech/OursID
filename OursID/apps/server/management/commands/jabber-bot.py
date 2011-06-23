import datetime, os

from django.core.management.base import BaseCommand
from django.utils import daemonize

from server.models import OidRequest
from account.models import UserProfile
from settings import JABBER_ID, JABBER_PWD

from jabberbot.jabberbot import JabberBot, botcmd
from xmpp.protocol import JID

class Command(BaseCommand):
    help = 'Start Jabber notification bot'

    def handle(self, *args, **options):
        daemonize.become_daemon()
        #fp = open('/tmp/jabber-bot.pid', "w")
        #fp.write("%d\n" % os.getpid())
        #fp.close()
        bot = JabberNotificationBot(JABBER_ID,JABBER_PWD)
        bot.serve_forever()

class JabberNotificationBot(JabberBot):

    @botcmd
    def yes( self, mess, args):
        """Accept OpenID authentification request"""
        return self.setOidResquestState(mess, OidRequest.VALIDATION_ACCEPTED)

    @botcmd
    def no( self, mess, args):
        """Refuse OpenID authentification request"""
        return self.setOidResquestState(mess, OidRequest.VALIDATION_REFUSED)
        
    def setOidResquestState( self, mess, state):
        jid = JID(mess.getFrom())
        n_id = jid.getStripped()
        try:
            oidrequest = OidRequest.objects.filter(identity__userprofile__notification_id=n_id, identity__userprofile__notification_type=UserProfile.JABBER_NOTIFICATION_TYPE, identity__userprofile__notification_state=UserProfile.VALID_NOTIFICATION_STATE).latest('date_created')
            oidrequest.validation = state
            oidrequest.save()
            return 'OK'
        except OidRequest.DoesNotExist:
            return 'Error: couldn\'t find any OpenID request pending!'

    def unknown_command(self, mess, cmd, args):
        return 'Unknown command!'
