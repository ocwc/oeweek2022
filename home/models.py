from django.db import models

from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class HomePage(Page):
    """
    Home page, a.k.a. About page:
    - main section
    - "call to action section" (to the left from the main)
    - "anniversary" section (bellow the previous two)
    - "social media" section (TODO later, probably hardcoded)
    - "newsletter" section (TODO later, probably hardcoded)
    - "more details" section
    - "ways to contribute" section (TODO later, probably hardcoded)
    - "activities" section (TODO later, probably hardcoded)
    """

    main_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Main image",
    )
    main_intro = RichTextField(
        null=True, blank=True, max_length=1000, help_text="Main intro"
    )
    main_body = RichTextField(
        null=True, blank=True, max_length=1000, help_text="Main body"
    )

    cta_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text='"Call to action" image',
    )
    cta_title = models.CharField('"Call to action" title', null=True, max_length=254)
    cta_body = RichTextField(
        null=True, blank=True, max_length=1000, help_text='"Call to action" body'
    )
    cta_faq = models.CharField(
        default="FAQ",
        verbose_name="FAQ link text",
        max_length=255,
        help_text="Text to display on FAQ link",
    )
    cta_faq_link = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="FAQ page link",
        help_text="Choose a page to link to for the FAQ",
    )

    anniversary_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Anniversary image",
    )

    md_body = RichTextField(null=True, blank=True, help_text='"More details" body')

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("main_image"),
                FieldPanel("main_intro"),
                FieldPanel("main_body"),
            ],
            heading="Main section",
        ),
        MultiFieldPanel(
            [
                FieldPanel("cta_image"),
                FieldPanel("cta_title"),
                FieldPanel("cta_body"),
                MultiFieldPanel(
                    [
                        FieldPanel("cta_faq"),
                        FieldPanel("cta_faq_link"),
                    ]
                ),
            ],
            heading='"Call to action" section',
        ),
        MultiFieldPanel(
            [
                FieldPanel("anniversary_image"),
            ],
            heading="Anniversary section",
        ),
        MultiFieldPanel(
            [
                FieldPanel("md_body"),
            ],
            heading='"More details" section',
        ),
    ]

    def __str__(self):
        return "home page: %s" % self.title
