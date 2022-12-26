from django.urls import path

import contributor_profile.views as views

app_name = "contributor_profile"

urlpatterns = [
    path(
        "",
        views.view_profile,
        name="view",
    ),
    # path('edit/', ProfileEdit.as_view(), name='login_sent'),
    # path('calendar/', MyCalendar.as_view(), name='calendar'),
]
