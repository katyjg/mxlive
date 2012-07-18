from django.conf.urls.defaults import patterns, url
from django.contrib.auth.models import User
from django import forms
from django.conf import settings

import os

urlpatterns = patterns('imm.stats.views',
    (r'^$', 'stats_calendar', {}, 'stats-calendar-now'),
    (r'^(?P<month>\w+-\w+)/$', 'stats_calendar', {}, 'stats-calendar-any'),
    (r'^extras/(?P<year>\w+)-(?P<month>\w+)/$', 'stats_month', {}, 'stats-monthly'),
    (r'^beamline/(?P<year>\w+)/$', 'stats_year', {}, 'stats-yearly'),
    (r'^beamline/(?P<year>\w+)/usage.png$', 'stats_usage', {}, 'stats-usage-png'),
)