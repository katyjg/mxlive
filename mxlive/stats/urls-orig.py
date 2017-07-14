from django.conf.urls import url
from lims.models import Data
from lims.views import object_list
import views


urlpatterns = [
    url(r'^$', views.stats_calendar, {}, 'stats-calendar-now'),
    url(r'^(?P<month>\w+-\w+)/$', views.stats_calendar, {}, 'stats-calendar-any'),
    url(r'^extras/(?P<year>\w+)-(?P<month>\w+)/$', views.stats_month, {}, 'stats-monthly'),
    url(r'^shifts/(?P<year>\w+)/$', views.stats_year, {}, 'stats-shifts'),
    url(r'^params/(?P<year>\w+)/$', views.stats_params, {}, 'stats-params'),
    url(r'^params/$', views.stats_params, {'cumulative': True}, 'stats-params-all'),
]
urlpatterns += [
    url(r'^dataset/$', object_list, {'model': Data, 'template': 'staff/lists/dataset_list.html', 'num_show': 99, 'view_only': True}, 'stats-data-list'),
]
