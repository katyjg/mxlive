from django.conf.urls.defaults import patterns
urlpatterns = patterns('messaging.views',
    (r'^(?P<id>\d+)/$', 'get_message'),
)
