# -*- coding: utf-8 -*-

import pytest

from web.models import Resource
from web.utils import guess_missing_location


def __prepare_resource(country=None, city=None):
    resource = Resource()
    resource.country = country
    resource.city = city
    resource.save()
    return resource.id


def __get_resource(id):
    return Resource.objects.get(pk=id)


@pytest.mark.django_db
def test_guess_missing_activity_fields_location():
    # fails to guess given Paris/France vs. Paris/Texas
    resource_id = __prepare_resource(city="Paris")
    guess_missing_location(resource_id)
    resource = __get_resource(resource_id)
    assert resource.lat is None
    assert resource.lng is None

    resource_id = __prepare_resource(city="Paris", country="United States")
    guess_missing_location(resource_id)
    resource = __get_resource(resource_id)
    assert resource.lat == 33.66094
    assert resource.lng == -95.55551

    resource_id = __prepare_resource(city="kosice")
    guess_missing_location(resource_id)
    resource = __get_resource(resource_id)
    assert resource.lat == 48.71395
    assert resource.lng == 21.25808

    resource_id = __prepare_resource(city="Dummy City")
    guess_missing_location(resource_id)
    resource = __get_resource(resource_id)
    assert resource.lat is None
    assert resource.lng is None
