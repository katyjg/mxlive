from django.conf.urls import patterns
from users.models import Data


urlpatterns = patterns('mxlive.stats.views',
    (r'^$', 'stats_calendar', {}, 'stats-calendar-now'),
    (r'^(?P<month>\w+-\w+)/$', 'stats_calendar', {}, 'stats-calendar-any'),
    (r'^extras/(?P<year>\w+)-(?P<month>\w+)/$', 'stats_month', {}, 'stats-monthly'),
    (r'^shifts/(?P<year>\w+)/$', 'stats_year', {}, 'stats-shifts'),
    (r'^params/(?P<year>\w+)/$', 'stats_params', {}, 'stats-params'),
    (r'^params/$', 'stats_params', {'cumulative': True}, 'stats-params-all'),    
)
urlpatterns += patterns('mxlive.users.views',
    (r'^dataset/$', 'object_list', {'model': Data, 'template': 'staff/lists/dataset_list.html', 'num_show': 99, 'view_only': True}, 'stats-data-list'),                        
)
