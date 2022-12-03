import django.utils.timezone as djtz
import geonamescache

from datetime import date
from django.conf import settings
from rest_framework_jwt.utils import jwt_payload_handler
from rest_framework_json_api.exceptions import exception_handler
from sentry_sdk import capture_message, set_context

from web.serializers import SubmissionResourceSerializer


GC = gc = geonamescache.GeonamesCache()


def custom_jwt_payload_handler(user):
    payload = jwt_payload_handler(user)

    payload["staff"] = user.is_staff
    return payload


def custom_drf_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if type(context.get("view").get_serializer_class()) == type(
        SubmissionResourceSerializer
    ):
        if hasattr(exc, "status_code") and exc.status_code != 404:
            set_context("submission", exc.get_full_details())
            capture_message(
                "Form Submission Validation Error",
                level="debug",
            )
    else:
        set_context("extra", exc.get_full_details())

        if hasattr(exc, "status_code") and exc.status_code != 404:
            capture_message("General DRF error", level="debug")
        else:
            capture_message("General DRF error", level="debug")

    return response


def days_to_go():
    now_utc = djtz.now().astimezone(djtz.utc)
    today = date(now_utc.year, now_utc.month, now_utc.day)
    future_oeweek = settings.FUTURE_OEWEEK
    delta_days = (future_oeweek - today).days
    # only return date if oeweek happens in less than a year AND more than a week
    if delta_days > 7 and delta_days < 365:
        return delta_days

    return None


def __noneOrEmpty(str):
    if str is None:
        return True
    if len(str.strip()) <= 0:
        return True
    return False


def _guess_missing_timezone(resource):
    if resource.event_source_timezone != "" or (__noneOrEmpty(resource.city) and __noneOrEmpty(resource.country)):
        return

    # try fast(-er) matching ...
    cities = []
    if not __noneOrEmpty(resource.city):
        cities = GC.search_cities(resource.city)
        if len(cities) == 0:
            # ... and if fails, try slower matching
            cities = GC.search_cities(resource.city, case_sensitive=False)

    # easy case: we find just one city
    if len(cities) == 1:
        resource.event_source_timezone = cities[0]['timezone']
        return

    # complicated case: we find more cities or no city given => we try to figure it out via country
    if resource.country is not None:
        countries = gc.get_countries_by_names()
        if resource.country in countries:
            country = countries[resource.country]
            if len(cities) > 0:
                for city in cities:
                    if city['countrycode'] == country['iso']:
                        resource.event_source_timezone = city['timezone']
                        return
            else:
                cities = GC.get_cities_by_name(country['capital'])
                if len(cities) == 1:
                    city_dict = cities[0]
                    city_key = next(iter(city_dict))
                    resource.event_source_timezone = city_dict[city_key]['timezone']
                    return

    print("failed to guess timezone for %s" % resource.city)


def guess_missing_activity_fields(resource):
    _guess_missing_timezone(resource)
