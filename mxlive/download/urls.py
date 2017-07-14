from django.conf.urls import url
from download.views import send_png, send_archive, send_file, find_file

urlpatterns = [
    url(r'^files/(?P<key>[a-f0-9]{40})/(?P<path>[^.]+)\.tar\.gz$', send_archive),
    url(r'^files/(?P<pk>\d+)/(?P<path>.+)\.gif$', find_file),
    url(r'^data/(?P<key>[a-f0-9]{40})/(?P<path>[^.]+)\.tar\.gz$', send_archive, {'data_dir': True}),
    url(r'^images/(?P<key>[a-f0-9]{40})/(?P<path>.+)-(?P<brightness>\w{2})\.png$', send_png),
    url(r'^files/(?P<key>[a-f0-9]{40})/(?P<path>.+)$', send_file),
    url(r'^images/(?P<key>[a-f0-9]{40})/(?P<path>.+\.(?:(?:img)|(?:cbf)))$', send_file),
]
