from django.urls import re_path, path
from . import views


def keyed_url(regex, view, kwargs=None, name=None):
    regex = r'(?P<signature>(?P<username>[\w_-]+):.+)/' + regex[1:]
    return re_path(regex, view, kwargs, name)


urlpatterns = [
    re_path(r'^accesslist/$', views.AccessList.as_view()),
    path('keys/<slug:username>', views.SSHKeys.as_view(), name='project-sshkeys'),

    keyed_url(r'^data/(?P<beamline>[\w_-]+)/$', views.AddData.as_view()),
    keyed_url(r'^report/(?P<beamline>[\w_-]+)/$', views.AddReport.as_view()),

    keyed_url(r'^project/$', views.UpdateUserKey.as_view(), name='project-update'),
    keyed_url(r'^samples/(?P<beamline>[\w_-]+)/$', views.ProjectSamples.as_view(), name='project-samples'),
    keyed_url(r'^launch/(?P<beamline>[\w_-]+)/(?P<session>[\w_-]+)/$', views.LaunchSession.as_view(), name='session-launch'),
    keyed_url(r'^close/(?P<beamline>[\w_-]+)/(?P<session>[\w_-]+)/$', views.CloseSession.as_view(), name='session-close'),
]