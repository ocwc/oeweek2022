import django_filters

from .data import LANGUAGE_CHOICES_FILTER, OPENTAGS_CHOICES
from .models import Resource


class AssetFilter(django_filters.FilterSet):
    language = django_filters.ChoiceFilter(
        field_name="form_language", choices=LANGUAGE_CHOICES_FILTER, label="Language"
    )
    opentags = django_filters.ChoiceFilter(
        field_name="opentags_csv",
        choices=OPENTAGS_CHOICES,
        lookup_expr="contains",
        label="Open Tags",
    )
    year = django_filters.ModelChoiceFilter(
        queryset=Resource.objects.values_list("year", flat=True)
        .distinct("year")
        .order_by("-year"),
        distinct=True,
    )

    class Meta:
        title = Resource
        fields = [
            "form_language",
            "opentags_csv",
            "year",
        ]


class EventFilter(django_filters.FilterSet):
    language = django_filters.ChoiceFilter(
        field_name="form_language", choices=LANGUAGE_CHOICES_FILTER, label="Language"
    )
    year = django_filters.ModelChoiceFilter(
        queryset=Resource.objects.values_list("year", flat=True)
        .distinct("year")
        .order_by("-year"),
        distinct=True,
    )

    class Meta:
        title = Resource
        fields = [
            "form_language",
            "year",
        ]
