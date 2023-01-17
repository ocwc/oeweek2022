from django import forms
from django.forms import ModelForm
from .models import Resource
from .data import COUNTRY_CHOICES


class ActivityForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['firstname'].widget.attrs.update({'class': 'mycustomclass'})

    class Meta:
        model = Resource
        fields = [
            # 'uuid',
            "post_type",  # event vs. resource
            "firstname",
            "lastname",
            "email",
            "twitter_personal",
            "twitter_institution",
            "institution",
            "institution_url",
            "institution_is_oeg_member",
            "country",
            "city",
            # 'event_type', # OPTIONS: local / online / anytime (asynchronous)
            "title",
            "event_facilitator",
            "content",  # 'DESCRIPTION',
            "event_time",  # event_source_datetime
            "link",
            "linkwebroom",
            "form_language",  # 'language',
            # 'opentags',
            # 'image',
            "user_image",
            "event_source_timezone",
            "newsletter",
        ]

    # uuid = forms.UUIDField(
    #     required = True,
    #     widget = forms.HiddenInput,
    # )

    post_type = forms.CharField(
        required=True,
        initial="event",
        widget=forms.HiddenInput,
    )

    firstname = forms.CharField(
        required=True,
        label="First Name (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    lastname = forms.CharField(
        required=True,
        label="Last Name (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    email = forms.CharField(
        required=True,
        label="Email (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    twitter_personal = forms.CharField(
        required=False,
        label="Personal Twitter",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    twitter_institution = forms.CharField(
        required=False,
        label="Organizational Twitter",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    institution = forms.CharField(
        required=True,
        label="Name of Institution, Organization, Initiative (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    institution_url = forms.CharField(
        required=True,
        label="Website of Institution, Organization, Initiative (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    institution_is_oeg_member = forms.TypedChoiceField(
        label="Is the organization an OEGlobal member?",
        coerce=lambda x: x == "True",
        choices=((None, "Please select an option below"), (False, "No"), (True, "Yes")),
    )

    # print(COUNTRY_CHOICES)
    # country = forms.ChoiceField(
    #     required=True,
    #     widget=forms.Select(
    #         choices=COUNTRY_CHOICES,
    #     ),
    # )

    city = forms.CharField(
        required=True,
        label="City, State (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    title = forms.CharField(
        required=True,
        label="Activity Title (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    event_facilitator = forms.CharField(
        required=False,
        label="Activity Facilitator",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    content = forms.CharField(
        required=True,
        label="Description (*)",
        widget=forms.Textarea(attrs={"class": "w-full"}),
    )

    link = forms.CharField(
        required=True,
        label="Link to the activity (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    linkwebroom = forms.CharField(
        required=False,
        label="Link to the webroom (if applicable)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    # firstname = forms.CharField(
    #     widget = forms.PasswordInput(
    #         attrs = {'class': 'errorlist'}
    #     )
    # )

    # firstname = forms.ChoiceField(
    #     widget   = forms.RadioSelect(
    #         attrs={
    #             'class': 'custom-control-input'
    #         }
    #     ),
    #     choices = (
    #         ('Peter', 'Blah Blah'),
    #     )
    # )

    user_image = forms.ImageField(
        required=False,
        label="Image",
    )

    event_source_timezone = forms.CharField(
        required=False,
        label="Event time zone",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )


class AssetForm(ModelForm):
    class Meta:
        model = Resource
        fields = [
            # 'uuid',
            "post_type",  # event vs. resource
            "firstname",
            "lastname",
            "email",
            "twitter_personal",
            "twitter_institution",
            "institution",
            "institution_url",
            "institution_is_oeg_member",
            "country",
            "city",
            "title",
            "content",  # 'DESCRIPTION',
            "link",
            "license",
            "form_language",  # 'language',
            # 'opentags',
            # 'image',
            "user_image",
            "event_source_timezone",
            "newsletter",
        ]

    # uuid = forms.UUIDField(
    #     required = True,
    #     widget = forms.HiddenInput,
    # )

    post_type = forms.CharField(
        required=True,
        initial="resource",
        widget=forms.HiddenInput,
    )

    firstname = forms.CharField(
        required=True,
        label="First Name (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    lastname = forms.CharField(
        required=True,
        label="Last Name (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    email = forms.CharField(
        required=True,
        label="Email (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    twitter_personal = forms.CharField(
        required=False,
        label="Personal Twitter",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    twitter_institution = forms.CharField(
        required=False,
        label="Organizational Twitter",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    institution = forms.CharField(
        required=True,
        label="Name of Institution, Organization, Initiative (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    institution_url = forms.CharField(
        required=True,
        label="Website of Institution, Organization, Initiative (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    institution_is_oeg_member = forms.TypedChoiceField(
        label="Is the organization an OEGlobal member?",
        coerce=lambda x: x == "True",
        choices=((None, "Please select an option below"), (False, "No"), (True, "Yes")),
    )

    # print(COUNTRY_CHOICES)
    # country = forms.ChoiceField(
    #     required=True,
    #     widget=forms.Select(
    #         choices=COUNTRY_CHOICES,
    #     ),
    # )

    city = forms.CharField(
        required=True,
        label="City, State (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    title = forms.CharField(
        required=True,
        label="Asset Title (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    content = forms.CharField(
        required=True,
        label="Description of Asset (*)",
        widget=forms.Textarea(attrs={"class": "w-full"}),
    )

    link = forms.CharField(
        required=True,
        label="Link to the asset (*)",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    # License (license)

    # Primary language (form_language)

    user_image = forms.ImageField(
        required=False,
        label="Image",
    )

    event_source_timezone = forms.CharField(
        required=False,
        label="Event time zone",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )


class ResourceFeedbackForm(ModelForm):
    class Meta:
        model = Resource
        fields = [
            "resource_id",  # event vs. resource
            "subject",
            "body",
        ]

    subject = forms.CharField(
        required=False,
        label="Subject",
        widget=forms.TextInput(attrs={"class": "w-full"}),
    )

    body = forms.CharField(
        required=False,
        label="Body",
        widget=forms.Textarea(attrs={"class": "w-full"}),
    )

    resource_id = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
    )
