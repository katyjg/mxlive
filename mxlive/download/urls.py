from django.conf.urls import patterns
from mxlive.download.views import send_png, send_archive, send_file, find_file

urlpatterns = patterns('',
    # Example:
    (r'^files/(?P<key>[a-f0-9]{40})/(?P<path>[^.]+)\.tar\.gz$', send_archive),
    (r'^files/(?P<pk>\d+)/(?P<path>.+)\.gif$', find_file),
    (r'^data/(?P<key>[a-f0-9]{40})/(?P<path>[^.]+)\.tar\.gz$', send_archive, {'data_dir': True}),
    (r'^images/(?P<key>[a-f0-9]{40})/(?P<path>.+)-(?P<brightness>\w{2})\.png$', send_png),
    (r'^files/(?P<key>[a-f0-9]{40})/(?P<path>.+)$', send_file),
    (r'^images/(?P<key>[a-f0-9]{40})/(?P<path>.+\.(?:(?:img)|(?:cbf)))$', send_file),
)
