import json
import uuid

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

from .data import COUNTRY_CHOICES, LANGUAGE_CHOICES, LICENSE_CHOICES

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

    POST_STATUS_DRAFT = "draft"
    POST_STATUS_PUBLISH = "publish"
    POST_STATUS_TRASH = "trash"
    POST_STATUS_TYPES = Choices(
        (POST_STATUS_PUBLISH, "Publish"),
        (POST_STATUS_DRAFT, "Draft"),
        (POST_STATUS_TRASH, "Trash"),
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
    event_time = models.DateTimeField(
        blank=True, null=True
    )  # in TZ set in setting.py:TIME_ZONE

    @property
    def event_time_link_to_everytimezone(self):
        ts = self.event_time
        noon_utc = ts.replace(hour=12, minute=0, second=0)
        offset = int((ts - noon_utc).total_seconds() / 60)
        return f"https://everytimezone.com/#{ts.year}-{ts.month}-{ts.day},{offset},6bj"

    @property
    def event_offset_in_hours(self):
        then = self.event_time
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

    event_type = models.CharField(
        max_length=255, blank=True, null=True, choices=EVENT_TYPES
    )
    event_online = models.BooleanField(default=False)
    # TODO 1: store original value filled by user (see then also event_source_timezone, given that Django will convert it to UTC before storing to `event_time`) *or* if too difficult, simply remove
    # TODO 2: once 1 is done, we can treat add migration which will treat empty event_source_datetime as "old content" and 1) copying `event_time` into `event_source_datetime` and 2) adjusting `event_time` to UTC assuming `event_source_timezone`
    event_source_datetime = models.CharField(max_length=255, blank=True)
    # TODO: store SESSION_TIMEZONE (see then also event_source_datetime) *or* if too difficult, simply remove
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

    # BEWARE: Before 2022, PostgreSQL was used and tags were stored in ArrayField (see commented-out
    # part bellow). For 2022 and 2023 SQlite is being used. Since SQlite does NOT support ArrayField,
    # only CharField is used. Later on we plan to move back to PostgreSQL (to take advantage of
    # MetaBase). And in the mean time we're importing pre-2022 content from PostgreSQL into SQlite,
    # hence:
    # 1) opentags_old = models.CharField is being added
    # 2) it will contain "SELECT ..., array_to_string(opentags, ',') AS opentags_old ..."
    # 3) once we migrate back to PostgreSQL, migration will be done using
    #    "SELECT string_to_array(opentags_old, ',') ..." and opentags_old will be removed
    # x) In the mean time, code working with 'opentags' will most probably NOT work since it was
    #    written for opentags = ArrayField
    opentags_old = models.CharField(max_length=255, blank=True)
    # opentags = ArrayField(
    #     models.CharField(
    #         max_length=255,
    #         blank=True,
    #     ),
    #     blank=True,
    # )
    @property
    def opentags(self):
        """temporary workaround until we are back to PostgreSQL with opentags = ArrayField"""
        return []

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
        2) user_image: user supplied (unauthenticated => untrusted), new for 2023
        3) image: supplied by OE Week admin(s), used in old OE Week Django implementation (2016)
        """

        u = self.image_url
        if u is None and self.user_image:
            u = self.user_image.url
        if u is None and self.image:
            u = self.image.image.url
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

    def send_new_submission_email(self):
        send_email_async(  # TODO: migrate away from django-mail-templated
            "emails/submission_received.tpl",
            {},
            "info@openeducationweek.org",
            [self.email],
        )

    def send_new_account_email(self, force=False):
        # TODO: check and possibly adjust how that should relate to magiclink accounts
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

            send_email_async(  # TODO: migrate away from django-mail-templated
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


class EmailQueueItem(models.Model):
    STATUS_UNSENT = "u"
    STATUS_SENT = "s"
    STATUS_CHOICES = Choices((STATUS_SENT, "sent"), (STATUS_UNSENT, "not sent yet"))

    subject = models.CharField(max_length=128)
    body = models.TextField()
    from_email = models.EmailField()
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    priority = models.IntegerField(default=1)
    status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=STATUS_UNSENT
    )
    # special case: we need to store list -> use json to serialize/deserialize into/from model
    # TODO: change to JSONField once we migrate back to PostgreSQL
    recipient_list = models.CharField(max_length=512)
    # special case: we need to store list -> use json to serialize/deserialize into/from model
    # TODO: change to JSONField once we migrate back to PostgreSQL
    cc = models.CharField(max_length=512, blank=True)

    def get_recipient_list(self):
        if self.recipient_list:
            return json.loads(self.recipient_list)
        return []

    def set_recipient_list(self, recipients):
        self.recipient_list = json.dumps(recipients)

    def get_cc(self):
        if self.cc:
            return json.loads(self.cc)
        return None

    def set_cc(self, cc):
        self.cc = json.dumps(cc)


def send_email_async(subject, body, from_email, recipient_list, cc=[], priority=1):
    """
    priority: 0 = notifications for staff, 1 = notifications for users
    """
    queue_item = EmailQueueItem.objects.create(
        subject=subject, body=body, from_email=from_email, priority=priority
    )
    queue_item.set_recipient_list(recipient_list)
    queue_item.set_cc(cc)
    queue_item.save()
    print("email %d put into the queue" % queue_item.id)


class EmailNotificationText(models.Model):
    ACTION_RES_APPROVED = "r_a"
    ACTION_RES_FEEDBACK = "r_f"
    ACTION_RES_REJECTED = "r_r"
    ACTION_CHOICES = Choices(
        (ACTION_RES_APPROVED, "resource: approved"),
        (ACTION_RES_FEEDBACK, "resource: feedback sent"),
        (ACTION_RES_REJECTED, "resource: rejected"),
    )

    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    subject = models.CharField(max_length=128)
    body = models.TextField(blank=True)


# TODO: Profile
# - map to a user account
# - add timezone setting
# - initial value (when signing up) of timezone settings comes from SESSION_TIMEZONE
# - when guessing tiemzone and user is logged in, use value from profile
# - timezone selection form will still override (in display) override profile value but changing it will affect only display, (e.g. NOT saved in profile, that is reserved only for "edit profile")
