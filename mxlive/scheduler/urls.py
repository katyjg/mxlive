from django.conf.urls.defaults import *

from views import current_week, get_shift_breakdown

urlpatterns = patterns('',
    url(r'^$', current_week, name='scheduler.thisweek'),
    url(r'^(?P<day>\d{4}-\d{2}-\d{2})/$', current_week, name='scheduler.anyweek'),
)
