from django.conf.urls.defaults import patterns
urlpatterns = patterns('dcss.views',
    (r'^(?P<path>\w+\.css)$', 'get_css'),
)
