from django.apps import AppConfig


class WebConfig(AppConfig):
    name = "web"
    verbose_name = "Main OE Week app"

    CLEANUP_TASK_NAME_V1 = "delete disabled magic links v1"

    def ready(self):
        from django_q.tasks import schedule, Schedule

        # FYI: try-except exists to avoid "sqlite3.OperationalError: no such table: django_q_schedule" during initial setup
        try:
            if Schedule.objects.filter(name=self.CLEANUP_TASK_NAME_V1).exists():
                return

            schedule(
                "web.magiclink_utils.delete_disabled_magic_links",
                name=self.CLEANUP_TASK_NAME_V1,
                schedule_type=Schedule.DAILY,
            )
        except:
            pass
