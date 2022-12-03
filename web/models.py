import hashlib
import requests
import uuid
from urllib.parse import urlencode
from base64 import urlsafe_b64encode

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.utils.text import slugify
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth import get_user_model

from taggit.managers import TaggableManager

from model_utils import Choices
from model_utils.models import TimeStampedModel

from mail_templated import send_mail

from .data import COUNTRY_CHOICES, LANGUAGE_CHOICES

import arrow

from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError

import django.utils.timezone as djtz

User = get_user_model()


class ReviewModel(models.Model):
    REVIEW_CHOICES = Choices(
        ("new", "New Entry"),
        ("feedback", "Requested feedback"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    )
    status = models.CharField(choices=REVIEW_CHOICES, default="new", max_length=16)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )

    class Meta:
        abstract = True


class Page(TimeStampedModel):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    content = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Category(TimeStampedModel):
    """Wordpress Category Taxonomy"""

    wp_id = models.IntegerField()
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)


def validate_image(image_obj):
    if (
        image_obj.width > settings.RESOURCE_IMAGE_MAX_WIDTH
        or image_obj.height > settings.RESOURCE_IMAGE_MAX_HEIGHT
    ):
        raise ValidationError(
            "Max image size size is %dx%d pixels"
            % (settings.RESOURCE_IMAGE_MAX_WIDTH, settings.RESOURCE_IMAGE_MAX_HEIGHT)
        )
    if image_obj.file.size > settings.RESOURCE_IMAGE_MAX_SIZE:
        raise ValidationError(
            "Max file size is %d MB"
            % (settings.RESOURCE_IMAGE_MAX_SIZE / (1024 * 1024))
        )


def validate_timezone(timezone_str):
    if not timezone:
        return
    try:
        timezone(timezone_str)
    except UnknownTimeZoneError:
        raise ValidationError("Unknown timezone")


@deconstructible
class UploadToResourceImageDir(object):
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        if instance.pk:
            new_name = "{}.{}".format(instance.pk, ext)
        else:
            new_name = "{}.{}".format(uuid.uuid4().hex, ext)
        return "{}/{}".format(self.sub_path, new_name)


class Resource(TimeStampedModel, ReviewModel):
    RESOURCE_TYPES = Choices(
        ("resource", "Resource"), ("project", "Project"), ("event", "Event")
    )

    POST_STATUS_TYPES = Choices(
        ("publish", "Publish"), ("draft", "Draft"), ("trash", "Trash")
    )

    EVENT_TYPES = Choices(
        # duplicated due to legacy choices
        ("conference/forum/discussion", "Conference/forum/discussion"),
        ("conference/seminar", "Conference/seminar"),
        ("workshop", "Workshop"),
        ("forum/panel/discussion", "Forum/panel/discussion"),
        ("other_local", "other_local"),
        ("local", "local"),
        ("webinar", "Webinar"),  # online
        ("discussion", "Online Discussion"),  # online
        ("other_online", "Other - Online"),  # online
        ("online", "Online Event"),
        ("anytime", "Anytime Event"),
    )

    # #djangomodels #validation #database <!--[[2022-01-23]]@`15:59:28Z`-->
    # Field.null // If True, Django will store empty values as NULL in the database. Default is False.
    # Field.blank // If True, the field is allowed to be blank. Default is False.
    # - blank=False, # required (default)
    # - blank=True, # optional
    # (...) I think this might not be clear for everyone: for a IntegerField to be nullable on both forms and db it is necessary to have both null=True and blank=True. See: https://code.djangoproject.com/wiki/NewbieMistakes#IntegerNULLS
    # JG: there is a #supercool table in #twoscoopsofdjango -- see screenshot in https://web.archive.org/web/20211112230210/https://stackoverflow.com/questions/4384098/in-django-models-py-whats-the-difference-between-default-null-and-blank

    uuid = models.UUIDField(
        blank=True,
        default=uuid.uuid4,
        # editable = False, # DO NOT USE -- non-editable fields cannot be used with forms
    )

    post_type = models.CharField(choices=RESOURCE_TYPES, max_length=25)
    post_status = models.CharField(choices=POST_STATUS_TYPES, max_length=25)
    post_id = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)

    form_id = models.IntegerField(blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True)

    firstname = models.CharField(max_length=255, blank=True, null=True)
    lastname = models.CharField(max_length=255, blank=True, null=True)

    email = models.EmailField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    institution_url = models.URLField(max_length=255, blank=True, null=True)
    institution_is_oeg_member = models.BooleanField(blank=True, null=True)
    form_language = models.CharField(
        max_length=255, blank=True, null=True, choices=LANGUAGE_CHOICES
    )

    LICENSE_CHOICES = Choices(
        ("Public domain", "Public domain"),
        ("CC-0", "CC Zero (CC 0)"),
        ("CC-BY", "CC Attribution (CC BY)"),
        ("CC-BY-SA", "CC Attribution — Share-Alike (CC BY-SA)"),
        ("CC-BY-NC", "CC Attribution — Non-Commercial (CC BY-NC)"),
        ("CC-NC-SA", "CC Attribution — Non-Commercial — Share-Alike (CC BY-NC-SA)"),
        ("Other", "Other open license"),
    )
    license = models.CharField(
        max_length=255, blank=True, null=True, choices=LICENSE_CHOICES
    )
    link = models.URLField(max_length=255, blank=True, null=True)
    linkwebroom = models.URLField(max_length=255, blank=True, null=True)

    image_url = models.URLField(blank=True, null=True, max_length=500)

    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(
        max_length=255, blank=True, null=True, choices=COUNTRY_CHOICES
    )
    event_time = models.DateTimeField(blank=True, null=True)

    @property
    def event_time_utc(self):
        try:
            event_tzinfo = timezone(self.event_source_timezone)
            event_localtime = self.event_time

            if event_localtime and event_tzinfo:
                dt = arrow.get(event_localtime, tzinfo=event_tzinfo)
                utc = dt.to("UTC")  # .replace(tzinfo=timezone('UTC'))
                return utc
        except:
            return ""
            # return self.event_time

    @property
    def event_time_link_to_everytimezone(self):
        ts = self.event_time_utc
        noon_utc = ts.replace(hour=12, minute=0, second=0)
        offset = int((ts - noon_utc).total_seconds() / 60)
        return f"https://everytimezone.com/#{ts.year}-{ts.month}-{ts.day},{offset},6bj"

    @property
    def event_offset_in_hours(self):
        then = self.event_time_utc
        now = djtz.now()

        duration = then - now
        duration_in_s = duration.total_seconds()
        hours = int(divmod(duration_in_s, 3600)[0])
        if hours == 1:
            return "in 1 hour"
        elif hours > 1 and hours <= 48:
            return "in " + str(hours) + " hours"
        else:
            return ""
        # FYI: https://stackoverflow.com/questions/1345827/how-do-i-find-the-time-difference-between-two-datetime-objects-in-python

    @property
    def event_day(self):
        return self.event_time_utc.strftime("%Y-%m-%d") if self.event_time_utc else ""

    @property
    def event_weekday(self):
        return self.event_time_utc.strftime("%A") if self.event_time_utc else ""

    @property
    def event_oeweekday(self):
        if not self.event_time_utc:
            return "Other"
        if arrow.get(self.event_time_utc) < arrow.get(
            settings.OEW_RANGE[0]
        ):  # .replace(tzinfo='local'):
            return "Other"
        if arrow.get(self.event_time_utc) > arrow.get(settings.OEW_RANGE[1]):
            return "Other"
        return self.event_time_utc.strftime("%A")

    event_type = models.CharField(
        max_length=255, blank=True, null=True, choices=EVENT_TYPES
    )
    event_online = models.BooleanField(default=False)
    event_source_datetime = models.CharField(max_length=255, blank=True)
    event_source_timezone = models.CharField(
        max_length=255, blank=True, validators=[validate_timezone]
    )
    event_directions = models.CharField(max_length=255, blank=True, null=True)
    event_other_text = models.CharField(max_length=255, blank=True, null=True)
    event_facilitator = models.CharField(max_length=255, blank=True, null=True)

    archive_planned = models.BooleanField(default=False)
    archive_link = models.CharField(max_length=255, blank=True)

    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    address = models.CharField(blank=True, max_length=1024)

    categories = models.ManyToManyField(Category, blank=True)
    tags = TaggableManager(blank=True)
    opentags = models.CharField(max_length=255, blank=True)

    # opentags = ArrayField(
    #     models.CharField(
    #         max_length=255,
    #         blank=True,
    #     ),
    #     blank=True,
    # )

    notified = models.BooleanField(default=False)
    raw_post = models.TextField(blank=True)

    screenshot_status = models.CharField(blank=True, default="", max_length=64)

    year = models.IntegerField(blank=True, null=True, default=settings.OEW_YEAR)
    oeaward = models.BooleanField(default=False)

    # supplied by site admins (e.g. OEG staff)
    image = models.ForeignKey(
        "ResourceImage", null=True, default=None, blank=True, on_delete=models.CASCADE
    )
    # supplied by contributors, unauthenticated
    user_image = models.ImageField(
        upload_to=UploadToResourceImageDir("images/resource/"),
        blank=True,
        validators=[validate_image],
    )

    twitter = models.CharField(blank=True, null=True, max_length=255)
    twitter_personal = models.CharField(blank=True, null=True, max_length=255)
    twitter_institution = models.CharField(blank=True, null=True, max_length=255)

    @property
    def twitter_personal_url(self):
        t = self.twitter_personal
        if t.startswith("https://twitter.com/"):
            return t
        elif t.startswith("@"):
            return "https://twitter.com/" + t[1:]
        else:
            return "https://twitter.com/" + t

    @property
    def twitter_personal_username(self):
        t = self.twitter_personal
        if t.startswith("https://twitter.com/"):
            return t[20:]
        elif t.startswith("@"):
            return t[1:]
        else:
            return t

    @property
    def twitter_institution_url(self):
        t = self.twitter_institution
        if t.startswith("https://twitter.com/"):
            return t
        elif t.startswith("@"):
            return "https://twitter.com/" + t[1:]
        else:
            return "https://twitter.com/" + t

    @property
    def twitter_institution_username(self):
        t = self.twitter_institution
        if t.startswith("https://twitter.com/"):
            return t[20:]
        elif t.startswith("@"):
            return t[1:]
        else:
            return t

    def __str__(self):
        return "Resource #{}".format(self.id)

    def get_full_url(self):
        if self.post_type == "event":
            return "http://www.openeducationweek.org/events/{}".format(self.slug)

        return "http://www.openeducationweek.org/resources/{}".format(self.slug)

    def get_image_url_for_detail(self):
        """We have (or can have) several images available for each resource. Hence
        this is the order of preference for actual use:

        1) image_url: supplied by OE Week admin(s), used in current OE Week Django implementation (2022)
        2) image: supplied by OE Week admin(s), used in old OE Week Django implementation (2016)
        3) user_image: user supplied (unauthenticated => untrusted), new for 2023

        TL;DR: Images supplied by untrusted anonymous users takes least precedence.
        """

        u = self.image_url
        if u is None and self.image:
            u = self.image.image.url
        if u is None and self.user_image:
            u = self.user_image.url
        return u

    def get_image_url_for_list(self):
        """Same as get_image_url_for_detail() but on-top of that does some "image size magic"
        for images hosted on archive.org ."""

        u = self.get_image_url_for_detail()
        if u and u.startswith("https://archive.org") and u.endswith(".png"):
            u = u[:-4] + "-sm.png"

        return u

    def get_image_url(self, request=None):
        u = self.get_image_url_for_detail()

        if request:
            try:
                return request.build_absolute_uri(self.image.image.url)
            except ValueError:
                return None
        else:
            return u

    def save(self, *args, **kwargs):
        if not self.slug:
            next = 0
            while (not self.slug) or (Resource.objects.filter(slug=self.slug).exists()):
                self.slug = slugify(self.title)

                if next:
                    self.slug += "-{0}".format(next)
                next += 1

        if self.firstname or self.lastname:
            self.contact = "{} {}".format(self.firstname, self.lastname)

        super().save(*args, **kwargs)

    def get_screenshot(self):
        def webshrinker_v2(access_key, secret_key, url, params):
            params["key"] = access_key
            request = "thumbnails/v2/{}?{}".format(
                urlsafe_b64encode(url.encode()).decode(), urlencode(params, True)
            )
            signed_request = hashlib.md5(
                "{}:{}".format(secret_key, request).encode("utf-8")
            ).hexdigest()

            return "https://api.webshrinker.com/{}&hash={}".format(
                request, signed_request
            )

        if self.image:
            self.screenshot_status = "DONE"
            return self.save()
        print(self.link)

        if self.link and self.screenshot_status in ["", "PENDING"]:
            api_url = webshrinker_v2(
                settings.WEBSHRINKER_KEY,
                settings.WEBSHRINKEY_SECRET,
                self.link,
                {"size": "3xlarge"},
            )
            print(api_url)
            response = requests.get(api_url)

            status_code = response.status_code

            if status_code == 200:
                resource_image = ResourceImage()
                resource_image.image.save(
                    "screenshot_{}.png".format(self.pk), ContentFile(response.content)
                )
                resource_image.save()

                self.image = resource_image
                self.screenshot_status = "DONE"
                self.save()
            elif status_code == 202:
                self.screenshot_status = "PENDING"
                self.save()
            else:
                print("Status code {}".format(response.status_code))
                raise NotImplementedError

    def send_new_submission_email(self):
        send_mail(
            "emails/submission_received.tpl",
            {},
            "info@openeducationweek.org",
            [self.email],
        )

    def send_new_account_email(self, force=False):
        email = self.email.lower()
        if force or not User.objects.filter(email=email).exists():
            user, is_created = User.objects.get_or_create(
                username=email,
                email=email,
                defaults={
                    "first_name": self.firstname[:30],
                    "last_name": self.lastname[:30],
                    "is_active": True,
                },
            )
            key = uuid.uuid4().hex
            user.set_password(key)
            user.save()

            send_mail(
                "emails/account_created.tpl",
                {"user": user, "key": key},
                "info@openeducationweek.org",
                [self.email],
            )


class EmailTemplate(models.Model):
    name = models.CharField(max_length=128)
    subject = models.CharField(max_length=255)
    body = models.TextField(
        help_text="You can use the following variables in body and title: {{title}}, {{name}}, {{link}}. HTML is not "
        "allowed. "
    )

    def __str__(self):
        return self.name


class ResourceImage(models.Model):
    image = models.ImageField(upload_to="images/", blank=True)

    def __str__(self):
        return repr(self.image)
