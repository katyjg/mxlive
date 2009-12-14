from django.conf.urls.defaults import *
urlpatterns = patterns('messaging.views',
    (r'^(?P<id>\d+)/$', 'get_message'),
)
