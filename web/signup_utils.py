from django.conf import settings


def inject_signup_switch(request):
    return {"signup_enabled": settings.SIGNUP_ENABLED}
