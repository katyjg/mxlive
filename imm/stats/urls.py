from django.conf.urls.defaults import patterns, url
from django.contrib.auth.models import User
from django import forms
from django.conf import settings

from lims.models import Data

import os

urlpatterns = patterns('imm.stats.views',
    (r'^$', 'stats_calendar', {}, 'stats-calendar-now'),
    (r'^(?P<month>\w+-\w+)/$', 'stats_calendar', {}, 'stats-calendar-any'),
    (r'^extras/(?P<year>\w+)-(?P<month>\w+)/$', 'stats_month', {}, 'stats-monthly'),
    (r'^shifts/(?P<year>\w+)/$', 'stats_year', {}, 'stats-shifts'),
    (r'^params/(?P<year>\w+)/$', 'stats_params', {}, 'stats-params'),
    (r'^params/$', 'stats_params', {'cumulative': True}, 'stats-params-all'),    
)
urlpatterns += patterns('imm.lims.views',
    (r'^dataset/$', 'object_list', {'model': Data, 'template': 'staff/lists/dataset_list.html', 'num_show': 99, 'view_only': True}, 'stats-data-list'),                        
)


