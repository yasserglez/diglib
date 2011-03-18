# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *


urlpatterns = patterns('diglib.views',
    (r'^$', 'main_page'),
)
