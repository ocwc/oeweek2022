import pytz
import os

import psycopg2

from datetime import datetime

from django.core.files import File
from django.core.management.base import BaseCommand
from django.conf import settings

from web.models import Resource, ResourceImage
from web.utils import get_gc_city_entry


class Command(BaseCommand):
    help = "Imports resources from old PostgreSQL oerweek2016 database"

    SERVER_TZ = pytz.timezone(settings.TIME_ZONE)

    def handle(self, *args, **options):
        conn = psycopg2.connect(settings.OERWEEK2016_DB_URL)
        curr = conn.cursor()

        # images:
        images = {}
        curr.execute("SELECT id, image FROM web_resourceimage")
        results = curr.fetchall()
        for (id, fn) in results:
            if len(fn) <= 0:
                continue
            if ResourceImage.objects.filter(image=fn).exists():
                print("WARNING, image %s already exists -> skipping" % fn)
                continue

            old_full_fn = os.path.join(settings.OLD_IMAGE_ROOT, fn)
            new_relative_fn = os.path.basename(fn)
            resource_image = ResourceImage()
            resource_image.image.save(new_relative_fn, File(open(old_full_fn, "rb")))
            resource_image.save()
            print(
                "image %s copied from %s to %s"
                % (fn, settings.OLD_IMAGE_ROOT, settings.MEDIA_ROOT)
            )
            images[id] = resource_image

        # resources:
        curr.execute(
            """SELECT
                created, modified, status, post_type, post_status, post_id, title, slug, content,
                form_id, contact, institution, form_language, license, link, reviewer_id, image_url,
                city, country, event_time, event_source_datetime, event_source_timezone, event_type,
                lat, lng, address, notified, email, archive_link, archive_planned, event_directions,
                event_online, institution_url, event_other_text, firstname, lastname, raw_post,
                event_facilitator, screenshot_status, year, linkwebroom,
                array_to_string(opentags, ',') AS opentags_old,
                oeaward,
                twitter AS twitter_institution,
                image_id
            FROM web_resource"""
        )
        results = curr.fetchall()
        for row in results:
            # handle info which is missing or needs adjustment:
            city = row[17]
            country = row[18]
            event_time = row[19]
            event_source_timezone = row[21]
            lat = row[23]
            lng = row[24]
            (
                event_time,
                event_source_timezone,
                lat,
                lng,
            ) = self.process_time_and_location(
                event_time, event_source_timezone, lat, lng, city, country
            )
            # store converted resource
            resource = Resource(
                created=row[0],
                modified=row[1],
                status=row[2],
                post_type=row[3],
                post_status=row[4],
                post_id=row[5],
                title=row[6],
                slug=row[7],
                content=row[8],
                form_id=row[9],
                contact=row[10],
                institution=row[11],
                form_language=row[12],
                license=row[13],
                link=row[14],
                reviewer_id=row[15],
                image_url=row[16],
                city=city,
                country=country,
                event_time=event_time,
                event_source_datetime=row[20],
                event_source_timezone=event_source_timezone,
                event_type=row[22],
                lat=lat,
                lng=lng,
                address=row[25],
                notified=row[26],
                email=row[27],
                archive_link=row[28],
                archive_planned=row[29],
                event_directions=row[30],
                event_online=row[31],
                institution_url=row[32],
                event_other_text=row[33],
                firstname=row[34],
                lastname=row[35],
                raw_post=row[36],
                event_facilitator=row[37],
                screenshot_status=row[38],
                year=row[39],
                linkwebroom=row[40],
                opentags_old=row[41],
                oeaward=row[42],
                twitter=row[43],
            )

            old_image_id = row[44]
            if old_image_id:
                if old_image_id in images:
                    resource.image = images[old_image_id]
                else:
                    print(
                        "WARNING, image id:%s NOT found (resource: %s) - SKIPPING image"
                        % (old_image_id, row[6])
                    )

            resource.save()
            print("resource: '%s' migrated" % row[6])

    def process_time_and_location(
        self, event_time, event_source_timezone, lat, lng, city, country
    ):
        """Convert old values into something which fits into 2023 model."""

        gc_city_entry = None

        if event_source_timezone == "I don't know":
            event_source_timezone = ""
        if event_source_timezone is None or event_source_timezone == "":
            gc_city_entry = get_gc_city_entry(country, city)
            if gc_city_entry:
                event_source_timezone = gc_city_entry["timezone"]

        # we have datetime as "2016-03-09 13:00:00+01" in PostgreSQL => convert to UTC
        if event_time:
            event_time = event_time.astimezone(self.SERVER_TZ)

        if lat is None and lng is None:
            if gc_city_entry is None:
                gc_city_entry = get_gc_city_entry(country, city)
            if gc_city_entry:
                lat = gc_city_entry["latitude"]
                lng = gc_city_entry["longitude"]

        return (event_time, event_source_timezone, lat, lng)
