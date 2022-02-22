# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

ALLOWED_HOSTS = ["api.openeducationweek.org", 'oeweek.oeglobal.org', 'oeweektest.oeglobal.org', 'localhost', '.lhr.life']

# Application definition

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "markdown",
    "taggit",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_auth",
    "django_wysiwyg",
    "ckeditor",
    "mail_templated",
    "model_utils",
    "corsheaders",
    "web",
    "import_export",
)

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    #"django.contrib.auth.middleware.SessionAuthenticationMiddleware", # (...) The SessionAuthenticationMiddleware class is removed. It provided no functionality since session authentication is unconditionally enabled in Django 1.10.
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
]

ROOT_URLCONF = "oerweekapi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "oerweekapi.wsgi.application"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

APPEND_SLASH = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = "/static/"
# STATIC_ROOT = os.path.join(BASE_DIR, "static")
# # STATIC_ROOT (...) The absolute path to the directory where collectstatic will collect static files for deployment.
# # STATICFILES_DIRS (...) Your project will probably also have static assets that aren’t tied to a particular app. In addition to using a static/ directory inside your apps, you can define a list of directories (STATICFILES_DIRS) in your settings file where Django will also look for static files.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "https://api.openeducationweek.org/media/"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_jwt.authentication.JSONWebTokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "PAGE_SIZE": 12,
    "EXCEPTION_HANDLER": "web.utils.custom_drf_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework_json_api.pagination.JsonApiPageNumberPagination",
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework_json_api.parsers.JSONParser",
        "rest_framework.parsers.FormParser",
        "rest_framework.parsers.MultiPartParser",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework_json_api.renderers.JSONRenderer",
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_METADATA_CLASS": "rest_framework_json_api.metadata.JSONAPIMetadata",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

# OLD: CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = [
    'https://oeweek.oeglobal.org',
    'https://oeweektest.oeglobal.org',
    'https://api.openeducationweek.org',
    'http://localhost:4200',
]

REST_USE_JWT = True

JWT_AUTH = {
    "JWT_ALLOW_REFRESH": True,
    "JWT_REFRESH_EXPIRATION_DELTA": datetime.timedelta(days=7),
    "JWT_LEEWAY": 60 * 5 * 60,
    "JWT_VERIFY_EXPIRATION": False,
    "JWT_EXPIRATION_DELTA": datetime.timedelta(days=7),
    "JWT_PAYLOAD_HANDLER": "web.utils.custom_jwt_payload_handler",
}

DJANGO_WYSIWYG_FLAVOR = "ckeditor"

LOGIN_URL = "/api-auth/login/"
OEW_YEAR = 2022
OEW_RANGE = ["2022-03-07 00:00:00", "2021-03-11 23:59:59"]
OEW_CFP_OPEN = "2022-01-08"
CI = os.environ.get("CI")
if CI:
    from .testsettings import *  # noqa: F401, F403
else:
    from .localsettings import *  # noqa: F401, F403

DEFAULT_AUTO_FIELD='django.db.models.AutoField'
