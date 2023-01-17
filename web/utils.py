import arrow
import django.utils.timezone as djtz

from datetime import date
from django.conf import settings
from rest_framework_jwt.utils import jwt_payload_handler
from rest_framework_json_api.exceptions import exception_handler
from sentry_sdk import capture_message, set_context

# special case for "front-end deployment" with "back-end stuff" not installed:
if not settings.FE_DEPLOYMENT:
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
    return __noneOrEmpty(resource.city) and __noneOrEmpty(resource.country)


def _set_location(resource, city):
    if _abort_needed(resource):
        print("guessing aborted (late): %d" % resource.id)
        return

    resource.lat = city["latitude"]
    resource.lng = city["longitude"]
    resource.save()
    print("guessing for %d: lat/lon: %s/%s" % (resource.id, resource.lat, resource.lng))


def get_gc_city_entry(country, city):
    # try fast(-er) matching ...
    cities = []
    if not __noneOrEmpty(city):
        cities = GC.search_cities(city)
        if len(cities) == 0:
            # ... and if fails, try slower matching
            cities = GC.search_cities(city, case_sensitive=False)

    # easy case: we find just one city
    if len(cities) == 1:
        return cities[0]

    # complicated case: we find more cities or no city given => we try to figure it out via country
    if country is not None:
        countries = GC.get_countries_by_names()
        if country in countries:
            country = countries[country]
            if len(cities) > 0:
                for city in cities:
                    if city["countrycode"] == country["iso"]:
                        return city
            else:
                cities = GC.get_cities_by_name(country["capital"])
                if len(cities) == 1:
                    city_dict = cities[0]
                    city_key = next(iter(city_dict))
                    return city_dict[city_key]

    return None


def guess_missing_location(resource_id):
    resource = Resource.objects.get(pk=resource_id)
    if _abort_needed(resource):
        print("guessing aborted (early): %d" % resource_id)
        return

    gc_city_entry = get_gc_city_entry(resource.country, resource.city)
    if gc_city_entry is None:
        print("failed to guess lat/lon for %s" % resource.city)
        return

    _set_location(resource, gc_city_entry)


def guess_missing_activity_fields_async(resource):
    if settings.FE_DEPLOYMENT:
        print(
            "WARNING, back-end stuff disabled => guessing of missing activity fields skipped"
        )
        return
    if _abort_needed(resource):
        return
    async_task(guess_missing_location, resource.id)
