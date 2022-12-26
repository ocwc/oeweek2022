from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from django.conf import settings


@login_required(login_url="magiclink:login")
def view_profile(request):
    return render(request, "contributor_profile/view.html")
