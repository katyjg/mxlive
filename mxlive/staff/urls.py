from django.conf.urls import url
from staff import views

urlpatterns = [
    url(r'^access/$', views.AccessList.as_view(), name='access-list'),
    url(r'^access/(?P<address>[.\d]+)/$', views.AccessEdit.as_view(), name='access-edit'),
    url(r'^users/$', views.ProjectList.as_view(), name='user-list'),
    url(r'^users/new/$', views.ProjectCreate.as_view(), name='new-project'),
    url(r'^announcement/(?P<pk>\d+)/edit/$', views.AnnouncementEdit.as_view(), name='announcement-edit'),
    url(r'^announcement/(?P<pk>\d+)/delete/$', views.AnnouncementDelete.as_view(), name='announcement-delete'),
]
