from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin

from django.urls import path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

# TODO: not sure about this one
# from search import views as search_views

from web import views

from django.views.generic.base import RedirectView

from rest_framework import routers
import rest_framework_jwt.views

from web.views import (
    PageViewSet,
    ResourceViewSet,
    EventViewSet,
    EventSummaryView,
    ExportResources,
    ResourceImageViewSet,
    SubmissionViewSet,
    TwitterSearchResults,
    EmailTemplateView,
    RequestAccessView,
)

router = routers.DefaultRouter(trailing_slash=False)
router.register(r"pages", PageViewSet, basename="Page")
router.register(r"resource", ResourceViewSet, basename="Resource")
router.register(r"resource-image", ResourceImageViewSet, basename="ResourceImage")
router.register(r"event", EventViewSet, basename="Event")
router.register(r"submission", SubmissionViewSet, basename="Submission")
router.register(r"email-templates", EmailTemplateView)

urlpatterns = (
    [
        url(r"^api/", include(router.urls)),
        url(r"^api/events-summary/", EventSummaryView.as_view()),
        url(r"^api/twitter/", TwitterSearchResults.as_view()),
        url(r"^api/request-access/", RequestAccessView.as_view()),
        url(r"^admin/", admin.site.urls),
        url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        url(r"^api-token-auth/", rest_framework_jwt.views.obtain_jwt_token),
        url(r"^api-token-refresh/", rest_framework_jwt.views.refresh_jwt_token),
        url(r"^export/resources/$", ExportResources.as_view(), name="resource_export"),
        url(r"^$", views.index, name="web_index"),
        url(r"^submit$", RedirectView.as_view(url="/contribute/", permanent=False)),
        url(r"^submit/$", RedirectView.as_view(url="/contribute/", permanent=False)),
        url(
            r"^submit-activity$",
            RedirectView.as_view(url="/contribute-activity/", permanent=False),
        ),
        url(
            r"^submit-activity/$",
            RedirectView.as_view(url="/contribute-activity/", permanent=False),
        ),
        url(
            r"^submit-asset$",
            RedirectView.as_view(url="/contribute-asset/", permanent=False),
        ),
        url(
            r"^submit-asset/$",
            RedirectView.as_view(url="/contribute-asset/", permanent=False),
        ),
        url(r"^contribute$", RedirectView.as_view(url="/contribute/", permanent=False)),
        url(
            r"^contribute-activity$",
            RedirectView.as_view(url="/contribute-activity/", permanent=False),
        ),
        url(
            r"^contribute-asset$",
            RedirectView.as_view(url="/contribute-asset/", permanent=False),
        ),
        url(r"^contribute/$", views.contribute),
        url(r"^contribute-activity/$", views.contribute_activity),
        path(
            "contribute-activity/<uuid:identifier>/",
            views.contribute_activity,
            name="contribute-activity",
        ),
        url(r"^contribute-asset/$", views.contribute_asset),
        path(
            "contribute-asset/<uuid:identifier>/",
            views.contribute_asset,
            name="contribute-asset",
        ),
        path("edit/<uuid:identifier>/", views.edit_resource),
        url(r"^thanks/$", views.thanks),
        url(r"^schedule$", RedirectView.as_view(url="/schedule/", permanent=True)),
        url(r"^schedule/$", RedirectView.as_view(url="/schedule/all/")),
        path(
            "schedule/<str:day>/",
            views.schedule_list,
            name="schedule_list",
        ),
        path(
            "schedule/toggle-favorite/<int:year>/<str:slug>/",
            views.toggle_favorite_event,
            name="toggle_favorite_event",
        ),
        url(r"^library$", RedirectView.as_view(url="/", permanent=True)),
        url(r"^library/$", RedirectView.as_view(url="/", permanent=True)),
        url(
            r"^library/events$",
            RedirectView.as_view(url="/library/events/", permanent=True),
        ),
        url(r"^library/events/$", views.show_events_library, name="library_events"),
        url(
            r"^library/resources$",
            RedirectView.as_view(url="/library/resources/", permanent=True),
        ),
        url(
            r"^library/resources/$",
            views.show_resources_library,
            name="library_resources",
        ),
        url(r"^events$", RedirectView.as_view(url="/events/", permanent=True)),
        url(r"^events/$", views.show_events),
        url(r"^resources$", RedirectView.as_view(url="/resources/", permanent=True)),
        url(r"^resources/$", views.show_resources),
        path("events/<str:slug>/", views.handle_old_event_detail),
        path(
            "events/<int:year>/<str:slug>/",
            views.show_event_detail,
            name="show_event_detail",
        ),
        path("resources/<str:slug>/", views.handle_old_resource_detail),
        path(
            "resources/<int:year>/<str:slug>/",
            views.show_resource_detail,
            name="show_resource_detail",
        ),
        path("staff/", views.staff_view, name="staff_view"),
        path(
            "staff/approve/<int:id>/",
            views.approve_action,
            name="staff_approve_action",
        ),
        path(
            "staff/submit_feedback/",
            views.submit_resource_feedback,
            name="staff_submit_feedback",
        ),
        path("cms/", include(wagtailadmin_urls)),
        path("documents/", include(wagtaildocs_urls)),
        # redirect from legacy URL path to new URLs
        url(r"^about$", RedirectView.as_view(url="/pages/about/", permanent=True)),
        url(r"^about/$", RedirectView.as_view(url="/pages/about/", permanent=True)),
        url(r"^promote$", RedirectView.as_view(url="/pages/promote/", permanent=True)),
        url(r"^promote/$", RedirectView.as_view(url="/pages/promote/", permanent=True)),
        url(r"^about/faq$", RedirectView.as_view(url="/pages/faq/", permanent=True)),
        url(r"^about/faq/$", RedirectView.as_view(url="/pages/faq/", permanent=True)),
        url(r"^about/2023$", RedirectView.as_view(url="/pages/2023/", permanent=True)),
        url(r"^about/2023/$", RedirectView.as_view(url="/pages/2023/", permanent=True)),
        # redirect from semi-hardcoded "about" page to the newer about page
        url(
            r"^pages$", RedirectView.as_view(url="/pages/about/", permanent=False)
        ),  # not permanent
        url(
            r"^pages/$", RedirectView.as_view(url="/pages/about/", permanent=False)
        ),  # not permanent
        # wagtail URLs
        path("pages/", include(wagtail_urls)),
        # path("search/", search_views.search, name="search"),
        url(r"^set-timezone/$", views.set_timezone, name="set_timezone"),
        url(
            r"^set-timezone-reload/$",
            views.set_timezone_and_reload,
            name="set_timezone_reload",
        ),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)

if settings.SIGNUP_ENABLED:
    urlpatterns += [
        path("auth/", include("magiclink.urls", namespace="magiclink")),
        path("profile/", include("contributor_profile.urls", namespace="c_profile")),
    ]
