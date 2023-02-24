import arrow
import bleach
import pytz
import urllib.parse
import twitter
import uuid
import xlwt

from itertools import groupby
from datetime import datetime, timezone
from enum import Enum

import django.utils.timezone as djtz

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import View

from braces.views import LoginRequiredMixin

from constance import config

from cryptography.fernet import InvalidToken

from django_htmx.middleware import HtmxDetails

from rest_framework import permissions, viewsets, generics, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .favorites_utils import (
    create_favorites,
    decode_favorites,
    encode_favorites,
    toggle_favorite,
)
from .filters import AssetFilter, EventFilter
from .forms import ActivityForm, AssetForm, ResourceFeedbackForm
from .models import (
    Page,
    Resource,
    ResourceImage,
    EmailNotificationText,
    EmailTemplate,
    send_email_async,
)
from .serializers import (
    PageSerializer,
    ResourceSerializer,
    SubmissionResourceSerializer,
    AdminSubmissionResourceSerializer,
    EmailTemplateSerializer,
    ResourceImageSerializer,
)
from .screenshot_utils import fetch_screenshot_async
from .timezone_utils import SESSION_TIMEZONE, TIMEZONE_CHOICES, get_timezone
from .utils import (
    contribution_period_is_now,
    days_to_go,
    guess_missing_activity_fields_async,
)


ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS
ALLOWED_TAGS += ["p"]

SESSION_LIBRARY_BOX_ASSET = "library_box_asset"
SESSION_LIBRARY_BOX_EVENT = "library_box_event"
SESSION_FAVORITES = "favorites"

LIBRARY_RESULTS_PER_PAGE = 16


def is_staff(user):
    return user.is_staff


def index(request):
    # if request.user.is_authenticated:
    #     return render(request, 'web/home.html', context={})
    # return HttpResponseRedirect('https://www.oeglobal.org/activities/open-education-week/')
    return render(request, "web/home.html", context={"days_to_go": days_to_go})


# def page__what_is_open_education_week(request):
#     return render(request, 'web/page--what-is-open-education-week.html')

# def page__faq(request):
#     return render(request, 'web/page--faq.html')

# def page__contribute(request):
#     return render(request, 'web/page--contribute.html')


def contribute(request):
    if contribution_period_is_now():
        return render(request, "web/contribute.html")
    else:
        return HttpResponseRedirect(reverse("web_index"))


def _set_session_tz_from_form_value(request):
    """Generally, we somehow guess timezone for users (their sessions) and then let them adjust that with SELECT
    at the bottom of all pages. Since 1) guess might be wrong and 2) users may overlook that option at the bottom,
    we "repeat" timezone SELECT in submit/edit activity form. But, we do not store that value into form/resource,
    we use it to set/reset timezone setting for the user in his session.

    Make sure to call this before processing the form, so that Django does timezone conversion properly,
    with the selected value.
    """
    tzname = request.POST.get("event_source_timezone")
    if tzname:
        request.session[SESSION_TIMEZONE] = tzname
        djtz.activate(pytz.timezone(tzname))


def _get_library_description_box_status(request, type):
    if type in request.session:
        return request.session[type]
    return True


def _set_library_description_box_status(request, type, value):
    request.session[type] = value


def contribute_activity(request, identifier=None):
    if not contribution_period_is_now():
        return HttpResponseRedirect(reverse("web_index"))
    if request.method == "POST":
        _set_session_tz_from_form_value(request)
        # create a form instance & populate with request data
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            print(form.cleaned_data)
            resource = form.save(commit=False)
            resource.content = bleach.clean(resource.content, tags=ALLOWED_TAGS)
            resource.save()
            guess_missing_activity_fields_async(resource)
            fetch_screenshot_async(resource)
            # process the data in form.cleaned_data as required
            # user = CustomUser.objects.create_user(
            #     form.cleaned_data['email'],
            #     form.cleaned_data['full_name'],
            # )
            context = {
                "uuid": str(resource.uuid),
                "title": resource.title,
                "contribute_similar": reverse(
                    "contribute-activity", args=[resource.uuid]
                ),
            }

            try:
                template = EmailNotificationText.objects.get(
                    action=EmailNotificationText.ACTION_RES_NEW
                )
                filled = template.fill_from_resource(resource)
                send_email_async(
                    filled["subject"],
                    filled["body"],
                    settings.EMAIL_NOTIF_FROM,
                    [resource.email],
                    cc=settings.EMAIL_NOTIF_CC,
                )
            except ObjectDoesNotExist as ex:
                print("WARNING failed to load template for email: %s" % ex)
            except Exception as ex:
                print("Failed to send email to %s: %s" % (resource.email, ex))

            return render(request, "web/thanks.html", context=context)
    elif identifier is not None:  # => GET ...
        resource = get_object_or_404(Resource, uuid=identifier)
        initial = {
            "post_type": resource.post_type,
            "firstname": resource.firstname,
            "lastname": resource.lastname,
            "email": resource.email,
            "twitter_personal": resource.twitter_personal,
            "twitter_institution": resource.twitter_institution,
            "institution": resource.institution,
            "institution_url": resource.institution_url,
            "institution_is_oeg_member": resource.institution_is_oeg_member,
            "country": resource.country,
            "city": resource.city,
            "title": "Copy of: " + resource.title,
            "event_facilitator": resource.event_facilitator,
            "content": "Copy of: " + resource.content,
            # "event_time": resource.event_time,
            "link": resource.link,
            "linkwebroom": resource.linkwebroom,
            "form_language": resource.form_language,
        }
        form = ActivityForm(initial=initial)
    else:
        form = ActivityForm()

    context = {
        "form": form,
        "action_verb": "Contribute",
        "submit_url": "/contribute-activity/",
    }
    return render(request, "web/contribute-activity.html", context)


def contribute_asset(request, identifier=None):
    if not contribution_period_is_now():
        return HttpResponseRedirect(reverse("web_index"))
    if request.method == "POST":
        # create a form instance & populate with request data
        form = AssetForm(request.POST, request.FILES)
        if form.is_valid():
            print(form.cleaned_data)
            resource = form.save(commit=False)
            resource.content = bleach.clean(resource.content, tags=ALLOWED_TAGS)
            resource.save()
            fetch_screenshot_async(resource)
            context = {
                "uuid": resource.uuid,
                "title": resource.title,
                "contribute_similar": reverse("contribute-asset", args=[resource.uuid]),
            }
            return render(request, "web/thanks.html", context=context)
    elif identifier is not None:  # => GET ...
        resource = get_object_or_404(Resource, uuid=identifier)
        initial = {
            "post_type": resource.post_type,
            "firstname": resource.firstname,
            "lastname": resource.lastname,
            "email": resource.email,
            "twitter_personal": resource.twitter_personal,
            "twitter_institution": resource.twitter_institution,
            "institution": resource.institution,
            "institution_url": resource.institution_url,
            "institution_is_oeg_member": resource.institution_is_oeg_member,
            "country": resource.country,
            "city": resource.city,
            "title": "Copy of: " + resource.title,
            "content": "Copy of: " + resource.content,
            "link": resource.link,
            "license": resource.license,
            "form_language": resource.form_language,
        }
        form = AssetForm(initial=initial)
    else:
        form = AssetForm()

    context = {
        "form": form,
        "action_verb": "Contribute",
        "submit_url": "/contribute-asset/",
    }
    return render(request, "web/contribute-asset.html", context)


# def page__materials(request):
#     return render(request, 'web/page--materials.html')


def edit_resource(request, identifier):
    uuid = identifier
    resource = Resource.objects.get(uuid=uuid)
    # form = ResourceForm(initial={'headline': 'Initial headline'}, instance=resource)
    if resource.post_type == "event":
        form = ActivityForm(instance=resource)
        template_url = "web/contribute-activity.html"
        contribute_similar_url = reverse("contribute-activity", args=[uuid])
    elif resource.post_type == "resource":
        form = AssetForm(instance=resource)
        template_url = "web/contribute-asset.html"
        contribute_similar_url = reverse("contribute-asset", args=[uuid])

    if request.method == "POST":
        _set_session_tz_from_form_value(request)

        if resource.post_type == "event":
            form = ActivityForm(request.POST or None, request.FILES, instance=resource)
        elif resource.post_type == "resource":
            form = AssetForm(request.POST or None, request.FILES, instance=resource)

        if form.is_valid():
            resource = form.save(commit=False)
            resource.content = bleach.clean(resource.content, tags=ALLOWED_TAGS)
            resource.save()
            return render(request, "web/updated.html")
        else:
            print(form.errors)

    context = {
        "form": form,
        "action_verb": "Edit",
        "submit_url": "/edit/" + str(uuid) + "/",
        "contribute_similar": contribute_similar_url,
    }
    return render(request, template_url, context)


def thanks(request):
    return render(request, "web/thanks.html")


def _init_oe_week_days():
    oe_week_days = []

    start_day = arrow.get(settings.OEW_RANGE[0])
    end_day = arrow.get(settings.OEW_RANGE[1])
    day = start_day
    while day < end_day:
        # TODO: use proper class instead of tuple, so that we can use say `name` instead of `1` in the code and templates
        oe_week_days.append(
            (day.format("dddd"), day.format("dddd, MMMM D"), day.format("d"))
        )
        day = day.shift(days=1)
    oe_week_days.append(("Other", "Other days", "other"))

    return oe_week_days


EO_WEEK_DAYS = _init_oe_week_days()


class ResourceOrdering(Enum):
    DEFAULT = 1
    LIBRARY = 2


def _set_event_day_number(event, tz):
    result = "other"
    if not event.event_time:
        return result

    oew_start = arrow.get(settings.OEW_RANGE[0], tzinfo=tz).datetime
    oew_end = arrow.get(settings.OEW_RANGE[1], tzinfo=tz).datetime
    if event.event_time >= oew_start and event.event_time <= oew_end:
        result = event.event_time.astimezone(tz).strftime("%w")

    event.event_day_number = result
    return event


def _get_events_query_set(
    year=None,
    id_filter=None,
    from_time=None,
    count_limit=None,
    ordering=ResourceOrdering.DEFAULT,
):
    result = Resource.objects.all().filter(post_type="event", post_status="publish")

    # filters (a.k.a. DB's WHERE)
    if year is not None:
        result = result.filter(year=year)
    if id_filter is not None:
        result = result.filter(id__in=id_filter)
    result = (
        result
        # TODO: very few items like that => try to sort that out without such excludes
        .exclude(event_source_timezone__exact="")
        .exclude(event_source_timezone__isnull=True)
        .exclude(event_time__isnull=True)
    )
    if from_time:
        result = result.filter(event_time__gte=from_time)

    # order
    if ordering == ResourceOrdering.LIBRARY:
        result = result.order_by("-year", Lower("title"))
    else:
        result = result.order_by("event_time", Lower("title"))

    # limit (after order)
    if count_limit:
        result = result[:count_limit]

    return result


def _get_events_list(
    request, event_day_number_filter=None, id_filter=None, favorites=None, year=None
):
    """
    Constructs event_list&co. with form and content adjusted to what we need in `show_events()` and `schedule_list()`.

    :param request:     request we're serving (for timezone info, etc.)
    :param event_day_number_filter: filter out events from other than given day (default: no filtering)
    :param id_filter:   use given list of event IDs (can be favorites list) to filter out all other IDs
    :param favorites:   use given favorites list (list of event IDs) to fill-in `favorite` flag (None = default = do NOT fill flag)
    :param year:        year for which to get a list (default: all years)
    :return:            (days_with_events, event_count)
    """
    event_list = _get_events_query_set(year=settings.OEW_YEAR, id_filter=id_filter)
    event_count = event_list.count()

    # fill in event day numbers based on timezone of the user, optionally also add `favorite` flag
    tz = pytz.timezone(get_timezone(request))
    for event in event_list:
        _set_event_day_number(event, tz)
        if favorites is not None:
            event.favorite = event.id in favorites

    # make a list of events per day
    event_list_per_day = {}
    for (_, _, number) in EO_WEEK_DAYS:
        if event_day_number_filter and event_day_number_filter != number:
            continue
        event_list_per_day[number] = []
    for event in event_list:
        if (
            event_day_number_filter
            and event_day_number_filter != event.event_day_number
        ):
            continue
        event_list_per_day[event.event_day_number].append(event)

    # merge event_list_per_day with EO_WEEK_DAYS, skip days with no events
    # (note: Yes, not very nice and efficient, but since day numbers depend in timezone from request ...)
    days_with_events = []
    for (name, name_date, number) in EO_WEEK_DAYS:
        if event_day_number_filter and event_day_number_filter != number:
            continue
        if event_day_number_filter is not None:
            # adjust event count if showing only subset
            event_count = len(event_list_per_day[number])
        if len(event_list_per_day[number]) <= 0:
            continue
        days_with_events.append((name, name_date, number, event_list_per_day[number]))

    return (days_with_events, event_count)


def show_events(request):
    (days_with_events, event_count) = _get_events_list(request, year=settings.OEW_YEAR)
    current_time_utc = djtz.now()
    comming_up_next_list = _get_events_query_set(
        year=settings.OEW_YEAR,
        from_time=current_time_utc,
        count_limit=settings.COMING_UP_NEXT_COUNT,
    )
    context = {
        "title": "OE Week %s Events" % settings.OEW_YEAR,
        "days_with_events": days_with_events,
        "comming_up_next_list": comming_up_next_list,
        "current_time_utc": current_time_utc,
        "event_count": event_count,
        "days_to_go": days_to_go,
        "reload_after_timezone_change": True,
    }
    return render(request, "web/events.html", context=context)


def show_events_library(request):
    """library: list of resources for all year"""
    f = EventFilter(
        request.GET, queryset=_get_events_query_set(ordering=ResourceOrdering.LIBRARY)
    )
    event_list = f.qs
    events_count_total = event_list.count()

    paginator = Paginator(event_list, LIBRARY_RESULTS_PER_PAGE)
    page = request.GET.get("page", 0)
    if page == 0:
        query_params = request.GET.copy()
        query_params["page"] = 1
        return HttpResponseRedirect(
            reverse("library_events") + "?" + query_params.urlencode()
        )
    try:
        event_list = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        raise Http404("Page not found.")

    current_time_utc = djtz.now()
    events_count = event_list.object_list.count()
    context = {
        "title": "Past Events",
        "current_time_utc": current_time_utc,
        "event_list": event_list,
        "event_count": events_count,
        "days_to_go": days_to_go,
        "filter": f,
        "paginator": paginator,
        "reload_after_timezone_change": True,
    }
    if events_count != events_count_total:
        context["events_count_total"] = events_count_total

    if _get_library_description_box_status(request, SESSION_LIBRARY_BOX_EVENT):
        context["show_description_box"] = True
    _set_library_description_box_status(request, SESSION_LIBRARY_BOX_EVENT, False)

    return render(request, "web/events-library.html", context)


def handle_old_event_detail(request, slug):
    resource = (
        Resource.objects.filter(slug=slug, post_type="event", post_status="publish")
        .order_by("year")
        .first()
    )
    if resource is None:
        raise Http404("No event matches given query.")
    return redirect("show_event_detail", year=resource.year, slug=resource.slug)


def show_event_detail(request, year, slug):
    event = get_object_or_404(Resource, year=year, slug=slug, post_type="event")
    if event.post_status != "publish" and not request.user.is_staff:
        raise Http404("Event %s/%s not found" % (year, slug))
    context = {
        "obj": event,
        "reload_after_timezone_change": True,
    }
    return render(request, "web/event_detail.html", context=context)


def _resources_query_set(year=None, ordering=ResourceOrdering.DEFAULT):
    result = Resource.objects.all().filter(post_type="resource", post_status="publish")

    # filters (a.k.a. DB's WHERE)
    if year is not None:
        result = result.filter(year=year)

    # order
    if ordering == ResourceOrdering.LIBRARY:
        result = result.order_by("-year", Lower("title"))
    else:
        result = result.order_by(Lower("title"))

    return result


def show_resources(request):
    """list of resources (assets) for current year"""
    resource_list = _resources_query_set(year=settings.OEW_YEAR)

    resource_count = resource_list.count()
    context = {
        "title": "OE Week %s Resources" % settings.OEW_YEAR,
        "resource_list": resource_list,
        "resource_count": resource_count,
        "days_to_go": days_to_go,
    }

    return render(request, "web/resources.html", context)


def show_resources_library(request):
    """library: list of resources for all year"""
    f = AssetFilter(
        request.GET, queryset=_resources_query_set(ordering=ResourceOrdering.LIBRARY)
    )
    resource_list = f.qs
    resource_count_total = resource_list.count()

    paginator = Paginator(resource_list, LIBRARY_RESULTS_PER_PAGE)
    page = request.GET.get("page", 0)
    if page == 0:
        query_params = request.GET.copy()
        query_params["page"] = 1
        return HttpResponseRedirect(
            reverse("library_resources") + "?" + query_params.urlencode()
        )
    try:
        resource_list = paginator.page(page)
    except (EmptyPage, PageNotAnInteger):
        raise Http404("Page not found.")

    resource_count = f.qs.count()
    resource_count = resource_list.object_list.count()
    context = {
        "title": "OE Week Library",
        "resource_list": resource_list,
        "resource_count": resource_count,
        "days_to_go": days_to_go,
        "filter": f,
        "paginator": paginator,
    }
    if resource_count != resource_count_total:
        context["resource_count_total"] = resource_count_total

    if _get_library_description_box_status(request, SESSION_LIBRARY_BOX_ASSET):
        context["show_description_box"] = True
    _set_library_description_box_status(request, SESSION_LIBRARY_BOX_ASSET, False)

    return render(request, "web/resources.html", context)


def handle_old_resource_detail(request, slug):
    resource = (
        Resource.objects.filter(slug=slug, post_type="resource", post_status="publish")
        .order_by("year")
        .first()
    )
    if resource is None:
        raise Http404("No resource matches given query.")
    return redirect("show_resource_detail", year=resource.year, slug=resource.slug)


def show_resource_detail(request, year, slug):
    resource = get_object_or_404(Resource, year=year, slug=slug, post_type="resource")
    if resource.post_status != "publish" and not request.user.is_staff:
        raise Http404("Event %s/%s not found" % (year, slug))
    context = {
        "obj": resource,
    }
    return render(request, "web/resource_detail.html", context=context)


SCHEDULE_DAY_ALL = "all"
SCHEDULE_DAY_MON = "mon"
SCHEDULE_DAY_TUE = "tue"
SCHEDULE_DAY_WED = "web"
SCHEDULE_DAY_THU = "thu"
SCHEDULE_DAY_FRI = "fri"
SCHEDULE_DAY_OTHER = "other"
SCHEDULE_DAYS = {
    # <day parameter of the view>: (<day param...>, <day number in EO_WEEK_DAYS>)
    SCHEDULE_DAY_ALL: (SCHEDULE_DAY_ALL, "all", "All Days"),
    SCHEDULE_DAY_MON: (SCHEDULE_DAY_MON, "1", "Mon"),
    SCHEDULE_DAY_TUE: (SCHEDULE_DAY_TUE, "2", "Tue"),
    SCHEDULE_DAY_WED: (SCHEDULE_DAY_WED, "3", "Wed"),
    SCHEDULE_DAY_THU: (SCHEDULE_DAY_THU, "4", "Thu"),
    SCHEDULE_DAY_FRI: (SCHEDULE_DAY_FRI, "5", "Fri"),
    SCHEDULE_DAY_OTHER: (SCHEDULE_DAY_OTHER, "other", "Other"),
}


def schedule_list(request, day):
    """schedule: list of events for given day in current year (=settings.OEW_YEAR)"""
    if day not in SCHEDULE_DAYS:
        raise Http404("Page not found.")
    show_only_day = SCHEDULE_DAYS[day][1]

    favorites = []
    if SESSION_FAVORITES in request.session:
        favorites = request.session[SESSION_FAVORITES]

    (days_with_events, event_count) = _get_events_list(
        request,
        event_day_number_filter=None if day == SCHEDULE_DAY_ALL else show_only_day,
        favorites=favorites,
        year=settings.OEW_YEAR,
    )

    current_time_utc = djtz.now()
    context = {
        "title": "Schedule %s" % settings.OEW_YEAR,
        "days_with_events": days_with_events,
        "current_time_utc": current_time_utc,
        "event_count": event_count,
        "days_to_go": days_to_go,
        "show_day": show_only_day,
        "schedule_days": SCHEDULE_DAYS.values(),
        "reload_after_timezone_change": True,
    }
    return render(request, "web/schedule.html", context=context)


def my_schedule_list(request):
    """my schedule: list of events in favorites list (in current session)"""
    favorites = []
    if SESSION_FAVORITES in request.session:
        favorites = request.session[SESSION_FAVORITES]
    (days_with_events, event_count) = _get_events_list(
        request, id_filter=favorites, favorites=favorites, year=settings.OEW_YEAR
    )

    my_favorites_permalink = None
    if len(favorites) > 0:
        encoded_favorites = encode_favorites(favorites)
        my_favorites_permalink = request.build_absolute_uri(
            reverse("custom_schedule_list", args=[encoded_favorites])
        )

    current_time_utc = djtz.now()
    context = {
        "title": "Schedule %s - My favorites" % settings.OEW_YEAR,
        "days_with_events": days_with_events,
        "current_time_utc": current_time_utc,
        "event_count": event_count,
        "days_to_go": days_to_go,
        "show_day": "my",  # hack/abuse, but allows us to use same schedule.html
        "schedule_days": SCHEDULE_DAYS.values(),
        "my_favorites_permalink": my_favorites_permalink,
        "reload_after_timezone_change": True,
    }
    return render(request, "web/schedule.html", context=context)


def custom_schedule_list(request, events):
    try:
        favorites_from_url = decode_favorites(events)
    except (InvalidToken, ValueError) as e:
        raise Http404("error", e)

    # give current user ability to see list created by someone else and see which events he/she already favorited and which not
    # note: Year skipped on purpose so as to allow users to see the lists also in the future, once the year when the list was created, passes.
    favorites_from_session = []
    if SESSION_FAVORITES in request.session:
        favorites_from_session = request.session[SESSION_FAVORITES]
    (days_with_events, event_count) = _get_events_list(
        request, id_filter=favorites_from_url, favorites=favorites_from_session
    )

    current_time_utc = djtz.now()
    context = {
        "title": "Schedule %s - Custom" % settings.OEW_YEAR,
        "days_with_events": days_with_events,
        "current_time_utc": current_time_utc,
        "event_count": event_count,
        "days_to_go": days_to_go,
        "show_day": "my",  # hack/abuse, but allows us to use same schedule.html
        "schedule_days": SCHEDULE_DAYS.values(),
        "reload_after_timezone_change": True,
    }
    return render(request, "web/schedule.html", context=context)


@user_passes_test(is_staff, login_url="/admin/")
def staff_view(request):
    """
    for now mainly "approval list"
    """
    request_timezone = request.GET.get("timezone", "local")
    resource_list = (
        Resource.objects.all()
        .filter(year=settings.OEW_YEAR)
        .filter(Q(post_status__in=["draft", ""]) | Q(status__in=["new", "feedback"]))
        .order_by("modified")
    )

    resource_count = len(resource_list)
    for resource in resource_list:
        url_args = [resource.year, resource.slug]
        if resource.post_type == "event":
            resource.detail_url = reverse("show_event_detail", args=url_args)
        else:
            resource.detail_url = reverse("show_resource_detail", args=url_args)

    current_time_utc = djtz.now()
    context = {
        "resource_list": resource_list,
        "current_time_utc": current_time_utc,
        "resource_count": resource_count,
        "reload_after_timezone_change": True,
        "oew_year": settings.OEW_YEAR,  # TODO: add also to other resource views, etc. to get rid of hard-coded "2023" in various templates
    }
    return render(request, "web/staff.html", context=context)


# see staff.html (and some others)
ACTION_BUTTON_NAME = "action"
APPROVE_ACTION_BUTTONS = {
    "approve": EmailNotificationText.ACTION_RES_APPROVED,
    "send feedback": EmailNotificationText.ACTION_RES_FEEDBACK,
    "reject": EmailNotificationText.ACTION_RES_REJECTED,
}


def _change_state(resource, action, reviewer):
    if action == EmailNotificationText.ACTION_RES_APPROVED:
        resource.post_status = Resource.POST_STATUS_PUBLISH
        resource.status = "approved"
    elif action == EmailNotificationText.ACTION_RES_FEEDBACK:
        resource.post_status = Resource.POST_STATUS_DRAFT
        resource.status = "feedback"
    elif action == EmailNotificationText.ACTION_RES_REJECTED:
        resource.post_status = Resource.POST_STATUS_TRASH
        resource.status = "rejected"
    else:
        raise ValueError("unknown action")
    resource.reviewer = reviewer
    resource.save()


@user_passes_test(is_staff, login_url="/admin/")
@require_POST
def approve_action(request, id):
    if ACTION_BUTTON_NAME not in request.POST:
        raise ValueError("missing action")
    action = request.POST["action"]
    if action not in APPROVE_ACTION_BUTTONS:
        raise ValueError("unknown action")
    action = APPROVE_ACTION_BUTTONS[action]

    resource = get_object_or_404(Resource, pk=id)
    template = get_object_or_404(EmailNotificationText, action=action)

    _change_state(resource, action, request.user)

    initial = template.fill_from_resource(resource)
    form = ResourceFeedbackForm(initial=initial)
    context = {
        "form": form,
        "resource": resource,
    }
    return render(request, "web/send-resource-feedback.html", context)


@user_passes_test(is_staff, login_url="/admin/")
@require_POST
def submit_resource_feedback(request):
    form = ResourceFeedbackForm(request.POST)
    resource_id = request.POST.get("resource_id")
    resource = get_object_or_404(Resource, pk=resource_id)
    if form.is_valid():
        if form.cleaned_data["body"]:
            send_email_async(
                form.cleaned_data["subject"],
                form.cleaned_data["body"],
                settings.EMAIL_NOTIF_FROM,
                [resource.email],
                cc=settings.EMAIL_NOTIF_CC,
            )
            return render(request, "web/resource-feedback-sent.html")
        # empty body => nothing to send => go straight back to ...
        return redirect("staff_view")

    context = {
        "form": form,
        "resource": resource,
    }
    return render(request, "web/send-resource-feedback.html", context)


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = "page_size"
    max_page_size = 10000
    page_query_param = "page[number]"


class CustomResultsSetPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 1000
    page_query_param = "page[number]"


class LargeMaxPageSizePagination(PageNumberPagination):
    max_page_size = 1000
    page_size_query_param = "page[size]"
    page_query_param = "page[number]"


class PageViewSet(viewsets.ModelViewSet):
    serializer_class = PageSerializer

    def get_queryset(self):
        queryset = Page.objects.all()
        if self.request.GET.get("slug"):
            queryset = queryset.filter(slug=self.request.GET.get("slug"))

        return queryset


class SubmissionPermission(permissions.BasePermission):
    message = "For changing submissions, you have to be logged-in"

    def has_permission(self, request, view):
        # We allow POST, since it's a `add` method, so users can submit form.
        if request.method == "POST" or request.method == "OPTIONS":
            return True

        if request.user.is_authenticated:
            return True

        return False


class SubmissionViewSet(viewsets.ModelViewSet):
    permission_classes = (SubmissionPermission,)
    pagination_class = CustomResultsSetPagination
    resource_name = "submission"

    def get_serializer_class(self):
        if self.request.user.is_superuser:
            return AdminSubmissionResourceSerializer

        return SubmissionResourceSerializer

    def get_queryset(self):
        queryset = Resource.objects.filter(
            created__gte=arrow.get(config.OEW_CFP_OPEN).datetime
        ).order_by("-created")
        if self.request.user.is_staff:
            return queryset

        return queryset.filter(email__iexact=self.request.user.email)


class ResourceEventMixin(generics.GenericAPIView):
    filterset_fields = ("slug", "form_language")

    def get_queryset(self, queryset):
        if self.request.GET.get("year"):
            year = self.request.GET.get("year", settings.OEW_YEAR)
            queryset = queryset.filter(year=year)

        if self.request.GET.get("opentags"):
            opentags = self.request.GET.get("opentags", "").split(",")
            queryset = queryset.filter(opentags__contains=opentags)

        return queryset


class ResourceViewSet(ResourceEventMixin, viewsets.ModelViewSet):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        queryset = Resource.objects.filter(
            post_status="publish", post_type__in=["resource", "project"]
        ).order_by("-id")

        return super().get_queryset(queryset)


class EventViewSet(ResourceEventMixin, viewsets.ModelViewSet):
    serializer_class = ResourceSerializer
    pagination_class = LargeMaxPageSizePagination
    resource_name = "event"

    def get_queryset(self):
        queryset = Resource.objects.filter(
            post_status="publish", post_type__in=["event"]
        )
        queryset = super().get_queryset(queryset)

        if self.request.GET.get("special") == "current":
            current_time = arrow.now().shift(hours=-1)
            queryset = Resource.objects.filter(
                event_type="online",
                event_time__gte=current_time.datetime,
                post_status="publish",
            ).order_by("event_time")[:8]
            return queryset

        event_type = self.request.GET.get("event_type")
        if event_type and len(event_type) == 1:
            event_type = event_type.pop()

        if event_type == "local":
            queryset = queryset.filter(year=settings.OEW_YEAR).exclude(
                Q(country="") | Q(event_type__in=("webinar", "online"))
            )

        if event_type == "online":
            queryset = queryset.filter(
                year=settings.OEW_YEAR,
                event_type__in=("webinar", "online", "other_online"),
            )

        if self.request.GET.get("date"):
            if self.request.GET.get("date") == "other":
                queryset = queryset.filter(event_time__month=3).exclude(
                    event_time__range=settings.OEW_RANGE
                )
            else:
                date = arrow.get(self.request.GET.get("date"))
                queryset = queryset.filter(
                    event_time__year=date.year,
                    event_time__month=date.month,
                    event_time__day=date.day,
                )

        return queryset.order_by("event_time")


class EventSummaryView(APIView):
    def get(self, request, format=None):
        summary = {}

        country_events = (
            Resource.objects.filter(post_type="event", modified__year=settings.OEW_YEAR)
            .exclude(country="", event_type__in=("webinar", ""))
            .order_by("country")
        )

        country_groups = []

        for k, g in groupby(country_events, lambda event: event.country):
            items = list(g)
            events = []
            for event in items:
                serialized = ResourceSerializer(event, context={"request": request})
                events.append(serialized.data)
            country_groups.append(events)

        summary["local_events"] = country_groups

        return Response(summary)


class ExportResources(LoginRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="application/ms-excel")
        response["Content-Disposition"] = "attachment; filename=oerweek-resources.xls"

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        datetime_style = xlwt.easyxf(num_format_str="dd/mm/yyyy hh:mm")

        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("Resources")

        row_num = 0

        columns = [
            ("ID", 2000),
            ("Resource Type", 6000),
            ("Title", 6000),
            ("Organization", 8000),
            ("Contact name", 8000),
            ("Email", 8000),
            ("OEW URL", 8000),
            ("Resources URL", 8000),
            ("Event Type", 8000),
            ("Date and Time", 8000),
            ("Country", 8000),
            ("City", 8000),
            ("Language", 8000),
            ("Twitter", 8000),
            ("Tags", 8000),
        ]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num][0], font_style)
            ws.col(col_num).width = columns[col_num][1]

        font_style = xlwt.XFStyle()
        font_style.alignment.wrap = 1

        for resource in Resource.objects.filter(
            post_status="publish", year=settings.OEW_YEAR
        ):
            row_num += 1

            event_time = ""
            if resource.event_time:
                # event_time = resource.event_time.strftime('%Y-%m-%d %H:%M')
                event_time = resource.event_time.replace(tzinfo=None)

            row = [
                resource.post_id,
                resource.post_type,
                urllib.parse.unquote(resource.title),
                resource.institution,
                resource.contact,
                resource.email,
                resource.get_full_url(),
                resource.link,
                resource.event_type,
                event_time,
                resource.country,
                resource.city,
                resource.form_language,
                resource.twitter,
                ", ".join(resource.opentags or []),
            ]

            for col_num in range(len(row)):
                if isinstance(row[col_num], datetime):
                    ws.write(row_num, col_num, row[col_num], datetime_style)
                else:
                    ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        return response


class TwitterSearchResults(APIView):
    def get(self, request, format=None):
        if cache.get("twitter", None):
            results = cache.get("twitter")
            return Response(results)

        twitter_api = twitter.Api(
            consumer_key=settings.TWITTER_API_KEY,
            consumer_secret=settings.TWITTER_API_SECRET,
            access_token_key=settings.TWITTER_ACCESS_TOKEN_KEY,
            access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        )

        api_results = twitter_api.GetSearch(
            raw_query="q=%23openeducationwk%2C%20OR%20%23oeglobal&result_type=mixed&count=100"
        )

        results = []
        for res in api_results:
            if not res.retweeted_status:
                results.append(
                    {"screen_name": res.user.screen_name, "id_str": res.id_str}
                )
        results = results[:4]

        cache.set("twitter", results, 60 * 5)
        return Response(results)


class EmailTemplateView(viewsets.ReadOnlyModelViewSet):
    model = EmailTemplate
    serializer_class = EmailTemplateSerializer
    queryset = EmailTemplate.objects.all().order_by("id")


class ResourceImageViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = (SubmissionPermission,)
    model = ResourceImage
    serializer_class = ResourceImageSerializer
    queryset = ResourceImage.objects.all().order_by("-id")


class RequestAccessView(APIView):
    permission_classes = (SubmissionPermission,)

    def post(self, request, format=None):
        email = request.data.get("email")

        try:
            print(email)
            resource = Resource.objects.filter(email=email)[0]
            resource.send_new_account_email(force=True)

        except IndexError:
            return Response({"status": "invalid_email"})

        return Response({"status": "ok"})


# HTMX stuff:

# Typing pattern recommended by django-stubs:
# https://github.com/typeddjango/django-stubs#how-can-i-create-a-httprequest-thats-guaranteed-to-have-an-authenticated-user
class HtmxHttpRequest(HttpRequest):
    htmx: HtmxDetails


# Used for pages which do NOT need to refresh their content when user chooses different timezone (e.g. anything but events pages).
# This is default behavior, e.g. relies on `reload_after_timezone_change` NOT being is set in the context or set to `False`.
# TODO: Currently not used (since selection was moved from footer to only events pages). For now kept, but if it stays that way, remove later.
@require_POST
def set_timezone(request: HtmxHttpRequest) -> HttpResponse:
    timezone = request.POST["timezone"]
    if timezone in TIMEZONE_CHOICES:
        request.session[SESSION_TIMEZONE] = request.POST["timezone"]
        result = "timezone changed: %s" % timezone
    else:
        result = "NOK"

    # special case: If user's first visit happens to be /library/events/, SESSION_LIBRARY_BOX_EVENT is set to False by timezone detection
    # immediately reloads the page hence afterwards no description box is shown. To counter that, we have this here:
    _set_library_description_box_status(request, SESSION_LIBRARY_BOX_EVENT, True)

    return render(
        request,
        "web/timezone.html",
        {"result": result},
    )


# Used for events pages (of wherever `reload_after_timezone_change:True` is set to context).
@require_POST
def set_timezone_and_reload(request: HtmxHttpRequest) -> HttpResponse:
    response = set_timezone(request)
    response["HX-Refresh"] = "true"
    return response


@require_POST
def toggle_favorite_event(request: HtmxHttpRequest, year, slug) -> HttpResponse:
    event = Resource.objects.get(
        post_type="event", post_status="publish", year=year, slug=slug
    )
    result = "fail"
    if event:
        if SESSION_FAVORITES not in request.session:
            favorites = create_favorites()
            request.session[SESSION_FAVORITES] = favorites
        else:
            favorites = request.session[SESSION_FAVORITES]

        result = toggle_favorite(favorites, event.id)
        request.session.modified = True

    return render(
        request,
        "web/toggle-favorite.html",
        {"favorited": result},
    )
