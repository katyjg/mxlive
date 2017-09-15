from django.conf.urls import url
from lims.models import Data, ScanResult, Result
from views import get_userlist
import views

def keyed_url(regex, *args):
    return (r'^(?P<key>[0-9A-F]{8}-[0-9A-F]{4}-4[0-9A-F]{3}-[89AB][0-9A-F]{3}-[0-9A-F]{12})/' + regex[1:],) + args



def keyed_url(regex, view, kwargs=None, name=None):
    regex = (r'(?P<signature>(?P<username>[\w_-]+):.+)/') + regex[1:]
    return url(regex, view, kwargs, name)


urlpatterns = [
    url(r'^accesslist/$', get_userlist),
    url(r'^accesslist/(?P<ipnumber>[.\d]+)/$', get_userlist),

    #keyed_url(r'^data/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', post_data_object, {'model': Data}),
    #keyed_url(r'^scan/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', post_data_object, {'model': ScanResult}),
    #keyed_url(r'^report/(?P<beamline>[\w_-]+)/(?P<project>[\w_-]+)/$', post_data_object, {'model': Result}),

    keyed_url(r'^project/$', views.UpdateUserKey.as_view(), name='project-update'),
    keyed_url(r'^samples/(?P<beamline>[\w_-]+)/$', views.ProjectSamples.as_view(), name='project-samples'),
    keyed_url(r'^launch/(?P<beamline>[\w_-]+)/(?P<session>[\w_-]+)/$', views.LaunchSession.as_view(), name='session-launch'),
    keyed_url(r'^close/(?P<beamline>[\w_-]+)/(?P<session>[\w_-]+)/$', views.CloseSession.as_view(), name='session-close'),
]
