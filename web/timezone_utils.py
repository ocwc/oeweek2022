import pytz

import django.utils.timezone as djtz


SESSION_TIMEZONE = "django_timezone"

TIMEZONE_CHOICES = sorted(pytz.common_timezones)


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tzname = request.session.get(SESSION_TIMEZONE)
        if tzname:
            djtz.activate(pytz.timezone(tzname))
        else:
            # TODO: try guessing timezone from IP, language, whatever
            djtz.deactivate()
        return self.get_response(request)


def inject_timezones(request):
    return {"timezones": TIMEZONE_CHOICES}
