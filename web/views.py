import arrow
import bleach
import pytz
import urllib.parse
import twitter
import uuid
import xlwt

from itertools import groupby
from datetime import datetime, timezone

from django.views.generic import View
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.db.models import Q
from django.db.models.functions import Lower
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from braces.views import LoginRequiredMixin

from django_htmx.middleware import HtmxDetails

from rest_framework import permissions, viewsets, generics, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .forms import ActivityForm, AssetForm
from .models import Page, Resource, ResourceImage, EmailTemplate
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

from mail_templated import send_mail

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

import django.utils.timezone as djtz


ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS
ALLOWED_TAGS += ["p"]


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
                "uuid": resource.uuid,
                "title": resource.title,
                "contribute_similar": reverse(
                    "contribute-activity", args=[resource.uuid]
                ),
            }

            try:
                send_mail(
                    "emails/submission_received.tpl",
                    context,  # {}, # {"user": user, "key": key},
                    "info@openeducationweek.org",
                    [resource.email],
                    cc=["openeducationweek@oeglobal.org"],
                )
            except:
                print("Failed to send email to " + resource.email)

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


# @login_required(login_url='/admin/')
def show_events(request):
    request_timezone = request.GET.get("timezone", "local")  # "local" = default
    event_list = (
        Resource.objects.all()
        .filter(post_type="event", post_status="publish", year=settings.OEW_YEAR)
        .exclude(event_source_timezone__exact="")
        .exclude(event_source_timezone__isnull=True)
        .exclude(event_time__isnull=True)
    )  # .exclude(post_status='trash')

    event_count = len(event_list)
    tz = pytz.timezone(get_timezone(request))
    for event in event_list:
        event.consolidated_image_url = event.get_image_url_for_list()
        _set_event_day_number(event, tz)

    # sort django queryset by UTC (property) values, not by local timezone
    event_list = sorted(event_list, key=lambda item: item.event_time)
    current_time_utc = djtz.now()
    days = [
        ("Monday", "Monday, March 6", "1"),
        ("Tuesday", "Tuesday, March 7", "2"),
        ("Wednesday", "Wednesday, March 8", "3"),
        ("Thursday", "Thursday, March 9", "4"),
        ("Friday", "Friday, March 10", "5"),
        # ('Saturday', 'Saturday, March 11', "6"),
        # ('Sunday', 'Sunday, March 12', "0"),
        ("Other", "Other days", "other"),
    ]

    context = {
        "days": days,
        "event_list": event_list,
        "current_time_utc": current_time_utc,
        "event_count": event_count,
        "days_to_go": days_to_go,
        "reload_after_timezone_change": True,
    }
    return render(request, "web/events.html", context=context)


# @login_required(login_url='/admin/')
def show_event_detail(request, year, slug):
    event = get_object_or_404(Resource, year=year, slug=slug)
    # #todo -- check if event is "published" (throw 404 for drafts / trash)
    event.consolidated_image_url = event.get_image_url_for_detail()
    context = {
        "obj": event,
        "reload_after_timezone_change": True,
    }
    return render(request, "web/event_detail.html", context=context)


# @login_required(login_url='/admin/')
def show_resources(request):
    resource_list = (
        Resource.objects.all()
        .filter(post_type="resource", year=settings.OEW_YEAR)
        .order_by(Lower("title"))
        .filter(post_status="publish")
    )  # .exclude(post_status='trash')
    # "Lower" = for case-insensitive sorting
    resource_count = len(resource_list)

    for resource in resource_list:
        resource.consolidated_image_url = resource.get_image_url_for_list()

    context = {
        "resource_list": resource_list,
        "resource_count": resource_count,
        "days_to_go": days_to_go,
    }
    return render(request, "web/resources.html", context=context)


# @login_required(login_url='/admin/')
def show_resource_detail(request, year, slug):
    resource = get_object_or_404(Resource, year=year, slug=slug)
    resource.consolidated_image_url = resource.get_image_url_for_detail()
    context = {"obj": resource}
    return render(request, "web/resource_detail.html", context=context)


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
            created__gte=arrow.get(settings.OEW_CFP_OPEN).datetime
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


@require_POST
def set_timezone(request: HtmxHttpRequest) -> HttpResponse:
    timezone = request.POST["timezone"]
    if timezone in TIMEZONE_CHOICES:
        request.session[SESSION_TIMEZONE] = request.POST["timezone"]
        result = "timezone changed: %s" % timezone
    else:
        result = "NOK"
    return render(
        request,
        "web/timezone.html",
        {"result": result},
    )


@require_POST
def set_timezone_and_reload(request: HtmxHttpRequest) -> HttpResponse:
    response = set_timezone(request)
    response["HX-Refresh"] = "true"
    return response
