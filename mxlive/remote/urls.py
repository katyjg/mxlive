from django.conf.urls import patterns
from lims.models import Data, ScanResult, Strategy, Result


def keyed_url(regex, *args):
    return (r'^(?P<key>[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12})/' + regex[1:],) + args


urlpatterns = patterns(
    'mxlive.remote.views',

    (r'^accesslist/$', 'get_userlist'),
    (r'^accesslist/(?P<ipnumber>[.\d]+)/$', 'get_userlist'),

    keyed_url(r'^samples/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', 'get_project_samples'),
    keyed_url(r'^data/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', 'post_data_object', {'model': Data}),
    keyed_url(r'^scan/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', 'post_data_object', {'model': ScanResult}),
    keyed_url(r'^report/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', 'post_data_object', {'model': Result}),
    keyed_url(r'^strategy/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', 'post_data_object', {'model': Strategy}),

)
