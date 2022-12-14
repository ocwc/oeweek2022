import arrow
import django.utils.timezone as djtz

from datetime import date
from django.conf import settings
from rest_framework_jwt.utils import jwt_payload_handler
from rest_framework_json_api.exceptions import exception_handler
from sentry_sdk import capture_message, set_context

from django_q.tasks import async_task

from .data import GC
from .models import Resource
from .serializers import SubmissionResourceSerializer


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
    today = arrow.utcnow().date()
    future_oeweek = settings.FUTURE_OEWEEK
    if today < arrow.get(settings.OEW_RANGE[1]).date():
        future_oeweek = arrow.get(settings.OEW_RANGE[0]).date()

    delta_days = (future_oeweek - today).days
    # only return date if oeweek happens in less than a year AND more than a week
    if delta_days > 7 and delta_days < 365:
        return delta_days

    return None


def contribution_period_is_now():
    now = arrow.utcnow()
    start = arrow.get(settings.OEW_CFP_OPEN).datetime
    end = arrow.get(settings.OEW_RANGE[1])
    return now >= start and now <= end


def __noneOrEmpty(str):
    if str is None:
        return True
    if len(str.strip()) <= 0:
        return True
    return False


def _abort_needed(resource):
    return resource.event_source_timezone != "" or (
        __noneOrEmpty(resource.city) and __noneOrEmpty(resource.country)
    )


def _set_timezone_and_location(resource, city):
    if _abort_needed(resource):
        print("guessing aborted (late): %d" % resource.id)
        return

    resource.event_source_timezone = city["timezone"]
    resource.lat = city["latitude"]
    resource.lng = city["longitude"]
    resource.save()
    print(
        "guessing for %d: timezone: %s, lat/lon: %s/%s"
        % (resource.id, resource.event_source_timezone, resource.lat, resource.lng)
    )


def guess_missing_timezone_and_location_async(resource_id):
    resource = Resource.objects.get(pk=resource_id)
    if _abort_needed(resource):
        print("guessing aborted (early): %d" % resource_id)
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
        _set_timezone_and_location(resource, cities[0])
        return

    # complicated case: we find more cities or no city given => we try to figure it out via country
    if resource.country is not None:
        countries = GC.get_countries_by_names()
        if resource.country in countries:
            country = countries[resource.country]
            if len(cities) > 0:
                for city in cities:
                    if city["countrycode"] == country["iso"]:
                        _set_timezone_and_location(resource, city)
                        return
            else:
                cities = GC.get_cities_by_name(country["capital"])
                if len(cities) == 1:
                    city_dict = cities[0]
                    city_key = next(iter(city_dict))
                    _set_timezone_and_location(resource, city_dict[city_key])
                    return

    print("failed to guess timezone for %s" % resource.city)


def guess_missing_activity_fields(resource):
    if _abort_needed(resource):
        return
    async_task(guess_missing_timezone_and_location_async, resource.id)
