from django.conf.urls.defaults import *
from django.conf import settings
from download.views import send_png, send_archive, send_file

urlpatterns = patterns('',
    # Example:
    (r'^files/(?P<key>[a-f0-9]{40})/(?P<path>.+)\.tar\.gz$', send_archive),
    (r'^images/(?P<key>[a-f0-9]{40})/(?P<path>.+)-(?P<brightness>\w{2})\.png$', send_png),
    (r'^files/(?P<key>[a-f0-9]{40})/(?P<path>.+)$', send_file),
    (r'^images/(?P<key>[a-f0-9]{40})/(?P<path>.+\.img)$', send_file),
)
