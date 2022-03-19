import django.utils.timezone as djtz

from datetime import date
from django.conf import settings
from rest_framework_jwt.utils import jwt_payload_handler
from rest_framework_json_api.exceptions import exception_handler
from sentry_sdk import capture_message, set_context


from web.serializers import SubmissionResourceSerializer


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
