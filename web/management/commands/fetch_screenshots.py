from django.core.management.base import BaseCommand
from django.conf import settings
from web.models import Resource
from web.screenshot_utils import fetch_screenshot_async


class Command(BaseCommand):
    help = "Fetches screenshots"

    def handle(self, *args, **options):
        for resource in Resource.objects.filter(
            screenshot_status__in=["", "PENDING"],
            year=settings.OEW_YEAR,
            post_status__in=["draft", "publish"],
        ):
            print(resource.id)
            # TODO: remove: resource.get_screenshot()
            fetch_screenshot_async(resource)
