from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from staff import views

urlpatterns = [
    url(r'^access/$', login_required(views.AccessList.as_view()), name='access-list'),
    url(r'^access/(?P<address>[.\d]+)/$', login_required(views.AccessEdit.as_view()), name='access-edit'),
    url(r'^users/$', login_required(views.ProjectList.as_view()), name='user-list'),
    url(r'^users/new/$', login_required(views.ProjectCreate.as_view()), name='new-project'),
]
