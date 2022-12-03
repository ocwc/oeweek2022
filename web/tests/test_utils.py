# -*- coding: utf-8 -*-

from web.models import Resource
from web.utils import guess_missing_activity_fields


def test_guess_missing_activity_fields():
    # several Bostons exist + no country given -> not able to guess
    resource = Resource()
    resource.city = "Boston"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == ""

    resource = Resource()
    resource.city = "Boston"
    resource.country = "United States"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == "America/New_York"

    resource = Resource()
    resource.city = "Bratislava"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == "Europe/Bratislava"

    resource = Resource()
    resource.city = "kosice"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == "Europe/Bratislava"

    # note: TODO later, but tricky, since:
    # 1) if we get "capital" for the country and look it up via get_cities_by_name(),
    #    we get several "Washington"
    # 2) even if we do filter properly, the result might be ambiguous anyway
    #    since there are several timezones in US
    resource = Resource()
    resource.country = "United States"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == ""

    resource = Resource()
    resource.country = "Slovakia"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == "Europe/Bratislava"

    resource = Resource()
    resource.city = "Dummy City"
    guess_missing_activity_fields(resource)
    assert resource.event_source_timezone == ""
