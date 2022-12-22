from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.search import index


class FaqIndexPage(Page):
    """
    FAQ index page
    """

    intro = RichTextField(max_length=1000, help_text="FAQ index page intro")

    content_panels = Page.content_panels + [FieldPanel("intro")]


class FaqPage(Page):
    """
    FAQ page

    We do not intend to have actual "one question, one answer" since we want just one single page,
    but for now this seems to be the way.
    """

    # page title serves as question
    answer = RichTextField(max_length=1000, help_text="Answer")
    # TODO: ordering, hence some number, ...?

    search_fields = Page.search_fields + [
        index.SearchField("answer"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("answer"),
    ]

    def __str__(self):
        return "FAQ page: %s" % self.title
