from django.conf.urls import url, patterns
from scheduler.views import current_week

urlpatterns = patterns('',
    url(r'^$', current_week, name='scheduler-thisweek'),
    url(r'^(?P<day>\d{4}-\d{2}-\d{2})/$', current_week, name='scheduler-anyweek'),
)


