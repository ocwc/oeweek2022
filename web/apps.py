import os
from sqlite3 import OperationalError

from django.apps import AppConfig
from django.conf import settings
from django.db.utils import ProgrammingError


class WebConfig(AppConfig):
    name = "web"
    verbose_name = "Main OE Week app"

    CLEANUP_SEND_EMAIL_QUEUE_TASK_NAME_V1 = "clean-up send email queue v1"
    CLEANUP_TASK_NAME_V1 = "delete disabled magic links v1"
    SEND_EMAIL_TASK_NAME_V1 = "send email v1"

    def schedule_task(self, function_name, task_name, schedule_type, minutes=None):
        from django_q.tasks import schedule, Schedule

        try:
            if Schedule.objects.filter(name=task_name).exists():
                return

            schedule(
                function_name,
                name=task_name,
                schedule_type=schedule_type,
                minutes=minutes,
            )
        except OperationalError:
            # to avoid "sqlite3.OperationalError: no such table: django_q_schedule" during initial setup
            # e.g. when we do NOT need full DEV setup with django-q fully operational
            print("ERROR: failed to schedule task %s" % task_name)
        except ProgrammingError:
            # to allow initial "manage migrate" when django_q do not exist yet
            print(
                "WARNING: failed to schedule task %s - django-q stuff in DB not initialized yet"
                % task_name
            )

    def ready(self):
        if settings.FE_DEPLOYMENT:
            print(
                "WARNING, back-end stuff disabled => scheduling of back-end tasks skipped"
            )
            return
        if not os.environ.get("RUN_MAIN"):
            print("not a main runserver => scheduling of back-end tasks skipped")
            return

        from django_q.tasks import Schedule

        self.schedule_task(
            "web.magiclink_utils.delete_disabled_magic_links",
            self.CLEANUP_TASK_NAME_V1,
            Schedule.DAILY,
        )
        self.schedule_task(
            "web.email_utils.send_email_task",
            self.SEND_EMAIL_TASK_NAME_V1,
            Schedule.MINUTES,
            minutes=1,
        )
        self.schedule_task(
            "web.email_utils.clean_send_email_queue",
            self.CLEANUP_SEND_EMAIL_QUEUE_TASK_NAME_V1,
            Schedule.DAILY,
        )
