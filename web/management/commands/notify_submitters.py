import time

from django.core.management.base import BaseCommand
from mail_templated import send_mail
from django.template.loader import get_template

from web.models import Resource


# TODO: since those works only for 2022, remove once 2023 submissions period is in progress
class Command(BaseCommand):
    help = "Notifies submitters that they got accepted"

    def handle(self, *args, **options):

        for resource in Resource.objects.filter(
                year=2022,
                # created__year=2022,
                post_status='publish',
                notified=False,
                # email='example@example.org',
        ):#.exclude(email='')[:10]:

            # an extra check, just in case...
            if resource.notified==True:
                print(f'Skipping {resource.email} about #{resource.id} (already notified)')
                continue

            if resource.post_type == 'event':
                slug1 = 'events'
            elif resource.post_type == 'resource':
                slug1 = 'resources'

            context = {
                'slug1': slug1,
                'year': resource.year,
                'slug2': resource.slug,
                'title': resource.title,
                'firstname': resource.firstname,
            }

            try:
                send_mail(
                    "emails/accepted.tpl",
                    context, # {}
                    "info@openeducationweek.org",
                    [resource.email],
                    cc=['openeducationweek@oeglobal.org'],
                )
                resource.notified = True
                resource.save()
                print(f'Emailed {resource.email} about #{resource.id}')
                time.sleep(2)
            except:
                print(f'Failed to email {resource.email} about #{resource.id}')
