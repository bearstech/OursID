from django.core.management.base import BaseCommand
from server.models import OidRequest
import datetime

class Command(BaseCommand):
    help = 'Cleanup old OpenID requests'

    def handle(self, *args, **options):
        limittime = datetime.datetime.now() - datetime.timedelta(minutes=5)
        OidRequest.objects.filter(date_created__lt=limittime).delete()
