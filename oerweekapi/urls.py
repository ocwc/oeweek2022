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
        # url(r'^api/submission/', SubmissionView.as_view()),
        url(r"^api/events-summary/", EventSummaryView.as_view()),
        url(r"^api/twitter/", TwitterSearchResults.as_view()),
        url(r"^api/request-access/", RequestAccessView.as_view()),
        url(r"^admin/", admin.site.urls),
        url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
        url(r"^api-token-auth/", rest_framework_jwt.views.obtain_jwt_token),
        url(r"^api-token-refresh/", rest_framework_jwt.views.refresh_jwt_token),
        path("auth/", include("magiclink.urls", namespace="magiclink")),
        url(r"^export/resources/$", ExportResources.as_view(), name="resource_export"),
        url(r"^$", views.index, name="web_index"),
        # url(r'^$', RedirectView.as_view(url='https://www.oeglobal.org/activities/open-education-week/', permanent=False), name='root_redirect'),
        # url(r'^page/what-is-open-education-week/$', views.page__what_is_open_education_week),
        # url(r'^page/faq/$', views.page__faq),
        # url(r'^page/contribute/$', views.page__contribute),
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
        # OLD: url(r'^edit/$', views.edit_resource),
        # url(r'^page/materials/$', views.page__materials),
        url(r"^thanks/$", views.thanks),
        url(r"^schedule$", RedirectView.as_view(url="/events/", permanent=False)),
        url(r"^schedule/$", RedirectView.as_view(url="/events/", permanent=False)),
        url(r"^events$", RedirectView.as_view(url="/events/", permanent=False)),
        url(r"^events/$", views.show_events),
        url(r"^resources$", RedirectView.as_view(url="/resources/", permanent=False)),
        url(r"^resources/$", views.show_resources),
        path("events/<int:year>/<str:slug>/", views.show_event_detail),
        path("resources/<int:year>/<str:slug>/", views.show_resource_detail),
        # url(r'^page/home/$', views.index, name='web_index'),
        path("cms/", include(wagtailadmin_urls)),
        path("documents/", include(wagtaildocs_urls)),
        # redirect from legacy URL path to new URLs
        url(r"^about$", RedirectView.as_view(url="/pages/", permanent=False)),
        url(r"^about/$", RedirectView.as_view(url="/pages/", permanent=False)),
        url(r"^about/faq/$", RedirectView.as_view(url="/pages/faq/", permanent=False)),
        url(
            r"^about/2023/$", RedirectView.as_view(url="/pages/2023/", permanent=False)
        ),
        path("pages/", include(wagtail_urls)),
        path("profile/", include("contributor_profile.urls", namespace="c_profile")),
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
