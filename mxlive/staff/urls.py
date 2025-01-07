from django.urls import re_path
from mxlive.staff import views

urlpatterns = [
    re_path(r'^access/$', views.AccessList.as_view(), name='access-list'),
    re_path(r'^access/(?P<address>[.\d]+)/$', views.AccessEdit.as_view(), name='access-edit'),
    re_path(r'^access/history/$', views.RemoteConnectionList.as_view(), name='connection-list'),
    re_path(r'^access/history/stats/$', views.RemoteConnectionStats.as_view(), name='connection-stats'),
    re_path(r'^access/connection/(?P<pk>\d+)/$', views.RemoteConnectionDetail.as_view(), name='connection-detail'),
    re_path(r'^users/$', views.ProjectList.as_view(), name='user-list'),
    re_path(r'^users/new/$', views.ProjectCreate.as_view(), name='new-project'),
    re_path(r'^users/(?P<username>[-\w]+)/$', views.UserStats.as_view(), name='user-detail'),
    re_path(r'^users/(?P<username>[-\w]+)/info/$', views.UserDetail.as_view(), name='user-info'),
    re_path(r'^users/(?P<username>[-\w]+)/delete/$', views.ProjectDelete.as_view(), name='user-delete'),
]