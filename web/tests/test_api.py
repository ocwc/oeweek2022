# -*- coding: utf-8 -*-
import os
import pytest
import json
import arrow

from pprint import pprint  # noqa: F401

from django.core import mail
from django.conf import settings

from web.models import Resource, ResourceImage


@pytest.mark.client
@pytest.mark.django_db
@pytest.mark.skip(reason="not working, needs update")
def test_submission_event_online(rf, client, db, normal_user):
    with open(
        os.path.join(settings.BASE_DIR, "web/tests/assets/sample-large.jpg"), "rb"
    ) as fp:
        response = client.post("/api/resource-image", {"image": fp})
        image_data = response.json()["data"]
        assert image_data["type"] == "ResourceImage"
        assert image_data["attributes"]["image"].startswith(
            "http://testserver/media/images/sample-large"
        )

    data = {
        "data": {
            "attributes": {
                "email": "mike.jones@example.com",
                "language": "German",
                "post_type": "event",
                "event_type": "online",
                "is_community": True,
                "institution": "OEC",
                "institutionurl": "http://www.oeconsortium.org",
                "directions": None,
                "archive": True,
                "link": "www.oeconsortium.org/events/online/20",
                "description": "Description of Webinar about OER",
                "country": "United States",
                "lastname": "Jones",
                "is_primary": False,
                "firstname": "Mike With A Very Long Last Name",
                "datetime": "2018-03-27T19:00:00+02:00",
                "is_higher": True,
                "title": "Webinar about OER",
                "city": "New York",
                "image_url": "",
                "opentags": ["Open Research", "Open Policy"],
                "image": image_data["id"],
            },
            "type": "submission",
        }
    }

    # client.login(username='user', password='password')
    response = client.post(
        "/api/submission",
        content_type="application/vnd.api+json",
        data=json.dumps(data),
    )
    assert data.get("data").get("attributes").get("title") in str(
        response.content
    ), "Submission failed"

    resource = Resource.objects.latest("id")
    assert resource.title == data.get("data").get("attributes").get("title")
    assert resource.content == data.get("data").get("attributes").get("description")
    assert resource.post_type == "event"
    assert resource.event_type == "online"
    assert resource.event_online is True
    assert resource.post_status == "draft"

    assert resource.image == ResourceImage.objects.latest("id")
    assert (
        response.json()["data"]["attributes"]["image_url"]
        == image_data["attributes"]["image"]
    )

    # check that validator adds http:// on www only submissions
    assert resource.link == "http://www.oeconsortium.org/events/online/20"
    assert resource.opentags == data.get("data").get("attributes").get("opentags")


@pytest.mark.client
@pytest.mark.django_db
@pytest.mark.skip(reason="not working, needs update")
def test_submission_event_local(rf, client, db, normal_user):
    data = {
        "firstname": "Ingrid",
        "lastname": "Rivers",
        "institution": "Good and Watson Associates",
        "institutionurl": "http://www.gof.com.au",
        "email": "jeper@mailinator.com",
        "country": "Antigua and Barbuda",
        "city": "Gregory Love",
        "language": "Armenian",
        "post_type": "event",
        "event_type": "local",
        "title": "Jakeem Owens",
        "description": "Et culpa sint hic enim omnis velit qui architecto autem atque rerum quis",
        "event_time": "2018-03-11T09:00:00.000Z",
        "event_facilitator": "Octavia Wagner",
        "directions": None,
        "link": "http://www.nonomitakiwu.com",
        "linkwebroom": "http://www.pom.cc",
        "opentags": ["Open Licenses"],
        "license": None,
        "post_status": "draft",
        "image_url": None,
        "slug": None,
    }

    client.login(username="user", password="password")
    client.post(
        "/api/submission", content_type="application/json", data=json.dumps(data)
    )

    resource = Resource.objects.latest("id")
    assert resource.title == data.get("title")
    assert resource.event_type == "local"
    assert resource.event_time == arrow.get(data.get("event_time")).datetime
    assert resource.event_facilitator == data.get("event_facilitator")


@pytest.mark.client
@pytest.mark.django_db
@pytest.mark.skip(reason="not working, needs update")
def test_submission_oer_resource(rf, client, db, normal_user):
    data = {
        "post_type": "resource",
        "city": "Washington, DC",
        "is_primary": False,
        "firstname": "Mike",
        "lastname": "Smith",
        "title": "Building for Scale: Updates to Google Maps APIs Standard Plan",
        "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit",
        "is_community": True,
        "country": "United States",
        "archive": False,
        "institution": "OEC",
        "link": "http://www.oeconsortium.org/web/resource/",
        "email": "mike3@example.com",
        "is_higher": True,
        "institutionurl": None,
        "language": "English",
        "datetime": "2018-03-27T00:00:00+02:00",
        "license": "CC-BY-SA",
        "directions": None,
        "linkwebroom": None,
        "opentags": ["Open Research", "Open Policy"],
        "event_facilitator": None,
        "event_type": None,
        "image_url": None,
        "twitter": None,
    }

    client.login(username="user", password="password")
    response = client.post(
        "/api/submission", content_type="application/json", data=json.dumps(data)
    )
    print(response.content)
    assert data.get("title") in str(response.content), "OER Resource Submission failed"

    resource = Resource.objects.latest("id")
    assert resource.title == data.get("title")
    assert (
        resource.slug == "building-for-scale-updates-to-google-maps-apis-standard-plan"
    )


@pytest.mark.client
@pytest.mark.django_db
@pytest.mark.skip(reason="not working, needs update")
def test_submission_project(rf, client, db, normal_user):
    data = {
        "archive": False,
        "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod"
        "\ntempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
        "veniam,\nquis nostrud exercitation ullamco laboris nisi ut aliquip ex ea"
        "commodo\nconsequat. Duis aute irure dolor in reprehenderit in voluptate "
        "velit esse\ncillum dolore eu fugiat nulla pariatur. Excepteur sint "
        "occaecat cupidatat non\nproident, sunt in culpa qui officia deserunt mollit"
        "anim id est laborum.",
        "city": "San Francisco, CA",
        "lastname": "Smith",
        "link": "http://www.oeconsortium.org/project/showcase/",
        "country": "United States",
        "institutionurl": "http://www.oeconsortium.org/",
        "language": "English",
        "is_higher": False,
        "datetime": "2018-03-27T00:00:00+02:00",
        "license": "Freely accessible",
        "institution": "OEC",
        "directions": None,
        "title": "Engineers Create The First Dust-Sized Wireless Sensors That Can Be Implanted Into The Human Body",
        "firstname": "Mike",
        "is_community": True,
        "is_primary": True,
        "email": "mike3@example.com",
        "contributiontype": "project",
        "opentags": ["Open Research", "Open Policy"],
        "post_type": "resource",
    }

    client.login(username="user", password="password")
    response = client.post(
        "/api/submission", content_type="application/json", data=json.dumps(data)
    )
    assert data.get("title") in str(response.content), "OER Resource Submission failed"

    resource = Resource.objects.latest("id")
    assert resource.title == data.get("title")


@pytest.mark.client
@pytest.mark.django_db
@pytest.mark.skip(reason="not working, needs update")
def test_submission_email(rf, client, db, normal_user):
    data = {
        "license": "other",
        "institution": "",
        "archive": True,
        "post_type": "event",
        "event_type": "local",
        "city": "London",
        "directions": None,
        "is_primary": False,
        "is_higher": True,
        "language": "English",
        "lastname": "Jones",
        "country": "United Kingdom",
        "email": "mike2@example.com",
        "firstname": "Mike",
        "title": "Building for Scale: Updates to Google Maps APIs Standard Plan",
        "datetime": "2018-03-27T00:00:00+02:00",
        "link": "",
        "description": "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod",
        "is_community": False,
        "institutionurl": "",
        "opentags": ["Open Research", "Open Policy"],
    }

    client.login(username="user", password="password")
    response = client.post(
        "/api/submission", content_type="application/json", data=json.dumps(data)
    )
    assert data.get("title") in str(response.content), "OER Resource Submission failed"

    assert len(mail.outbox) == 2
    assert mail.outbox[0].subject == "OE Week submission received"
    assert mail.outbox[1].subject == "OEW: Your account to edit submission(s)"


@pytest.mark.client
@pytest.mark.django_db
def test_exception_reporting(rf, client, db, normal_user):
    data = {
        "license": "other",
        "institution": "",
        "archive": True,
        "post_type": "event",
        "event_type": "local",
    }

    response = client.post(
        "/api/submission", content_type="application/json", data=json.dumps(data)
    )
    assert response.status_code == 400
