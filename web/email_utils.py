import pytz

from datetime import datetime, timedelta

from django.conf import settings
from django.core.mail import EmailMessage

from .models import EmailQueueItem


# how much messages to send in one minute (see scheduling of SEND_EMAIL_TASK_NAME_V1 in apps.py)
SEND_EMAIL_BATCH_SIZE = 10


def __process_email_queue_item(queue_item):
    email = EmailMessage(
        queue_item.subject,
        queue_item.body,
        queue_item.from_email,
        queue_item.get_recipient_list(),
        cc=queue_item.get_cc(),
    )
    count = email.send()
    if count > 0:
        print("email %d sent" % queue_item.id)
        queue_item.status = EmailQueueItem.STATUS_SENT
        queue_item.save()
    else:
        print("ERROR: failed to send email %d" % queue_item.id)


def send_email_task():
    for queue_item in EmailQueueItem.objects.filter(
        status=EmailQueueItem.STATUS_UNSENT
    ).order_by("priority", "modified", "id")[:SEND_EMAIL_BATCH_SIZE]:
        __process_email_queue_item(queue_item)


def list_queue():
    for queue_item in EmailQueueItem.objects.all().order_by(
        "created", "modified", "id"
    ):
        print(
            "%d: %s -> %s (cc: %s), status: %s, created: %s, modified: %s"
            % (
                queue_item.id,
                queue_item.from_email,
                queue_item.get_recipient_list(),
                queue_item.get_cc(),
                queue_item.status,
                queue_item.created,
                queue_item.modified,
            )
        )


def clean_send_email_queue():
    tzinfo = pytz.timezone(settings.TIME_ZONE)
    week_ago = datetime.now(tzinfo) - timedelta(days=7)
    count = EmailQueueItem.objects.filter(
        status=EmailQueueItem.STATUS_UNSENT, modified__lt=week_ago
    ).delete()[0]
    print("email queue clean-up: removed %d items" % count)


def mrproper():
    count = EmailQueueItem.objects.all().delete()[0]
    print("email queue major clean-up: removed %d items" % count)
