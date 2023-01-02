import pytz

from django.utils import timezone


SESSION_TIMEZONE = "django_timezone"

TIMEZONE_CHOICES = [
    # TODO: do a proper list, fox example from  zoneinfo.available_timezones(): https://docs.python.org/3/library/zoneinfo.html#zoneinfo.available_timezones
    ("America/New_York", "America/New_York"),
    ("Europe/Paris", "Europe/Paris"),
    ("UTC", "UTC"),
]


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.session.get(SESSION_TIMEZONE)
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            # TODO: try guessing timezone from IP, language, whatever
            timezone.deactivate()
        return self.get_response(request)


def inject_timezones(request):
    return {"timezones": TIMEZONE_CHOICES}
