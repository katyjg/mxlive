from django.conf.urls import url
from mxlive.staff import views

urlpatterns = [
    url(r'^access/$', views.AccessList.as_view(), name='access-list'),
    url(r'^access/(?P<address>[.\d]+)/$', views.AccessEdit.as_view(), name='access-edit'),
    url(r'^access/history/$', views.RemoteConnectionList.as_view(), name='connection-list'),
    url(r'^access/history/stats/$', views.RemoteConnectionStats.as_view(), name='connection-stats'),
    url(r'^access/connection/(?P<pk>\d+)/$', views.RemoteConnectionDetail.as_view(), name='connection-detail'),
    url(r'^users/$', views.ProjectList.as_view(), name='user-list'),
    url(r'^users/new/$', views.ProjectCreate.as_view(), name='new-project'),
    url(r'^users/(?P<username>[-\w]+)/$', views.UserStats.as_view(), name='user-detail'),
    url(r'^users/(?P<username>[-\w]+)/info/$', views.UserDetail.as_view(), name='user-info'),
    url(r'^users/(?P<username>[-\w]+)/delete/$', views.ProjectDelete.as_view(), name='user-delete'),
]
