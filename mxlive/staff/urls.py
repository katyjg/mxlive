from django.conf.urls import url
from lims import views

urlpatterns = [
    url(r'^$', views.staff_home, {}, 'staff-home'),
]