from django.conf.urls import url
from lims.models import Data, ScanResult, Result
from views import get_userlist, get_project_samples, post_data_object

def keyed_url(regex, *args):
    return (r'^(?P<key>[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12})/' + regex[1:],) + args


urlpatterns = [
    url(r'^accesslist/$', get_userlist),
    url(r'^accesslist/(?P<ipnumber>[.\d]+)/$', get_userlist),

    url(keyed_url(r'^samples/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$'), get_project_samples),
    url(keyed_url(r'^data/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$'), post_data_object, {'model': Data}),
    url(keyed_url(r'^scan/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$'), post_data_object, {'model': ScanResult}),
    url(keyed_url(r'^report/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$'), post_data_object, {'model': Result}),
]
