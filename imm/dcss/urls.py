from django.conf.urls.defaults import *
urlpatterns = patterns('dcss.views',
    (r'^(?P<path>\w+\.css)$', 'get_css'),
)
