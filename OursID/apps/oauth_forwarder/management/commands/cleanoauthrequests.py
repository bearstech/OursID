from django.core.management.base import BaseCommand
from oauth_forwarder.models import OAuthRequest
import datetime

class Command(BaseCommand):
    help = 'Cleanup old OAuth requests'

    def handle(self, *args, **options):
        limittime = datetime.datetime.now() - datetime.timedelta(minutes=5)
        OAuthRequest.objects.filter(date_created__lt=limittime).delete()
