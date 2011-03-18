# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponse

from diglib.models import Document


def main_page(request):
    return HttpResponse('Hello, World!')
