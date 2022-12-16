from django.db import models

from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from .blocks import BaseStreamBlock


class GenericPage(Page):
    """
    A generic content page for OE Week.
    """

    body = StreamField(
        BaseStreamBlock(),
        verbose_name="Generic page content block",
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    def __str__(self):
        return "generic page: %s" % self.title
