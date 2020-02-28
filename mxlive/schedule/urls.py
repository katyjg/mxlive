from django.conf.urls import url
from django.urls import path
from . import views, ajax_views


urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),

    path('beamlineproject/new/', views.BeamlineProjectCreate.as_view(), name='new-beamline-project'),
    path('beamlineproject/<int:pk>/edit/', views.BeamlineProjectEdit.as_view(), name='beamline-project-edit'),
    path('beamlineproject/<int:pk>/delete/', views.BeamlineProjectDelete.as_view(), name='beamline-project-delete'),
    path('beamtime/new/', views.BeamtimeCreate.as_view(), name='new-beamtime'),
    path('beamtime/<int:pk>/edit/', views.BeamtimeEdit.as_view(), name='beamtime-edit'),
    path('beamtime/<int:pk>/delete/', views.BeamtimeDelete.as_view(), name='beamtime-delete'),
    path('downtime/new/', views.DowntimeCreate.as_view(), name='new-downtime'),
    path('downtime/<int:pk>/edit/', views.DowntimeEdit.as_view(), name='downtime-edit'),
    path('support/new/', views.SupportCreate.as_view(), name='new-support'),
    path('support/<int:pk>/edit/', views.SupportEdit.as_view(), name='support-edit'),
    path('support/<int:pk>/delete/', views.SupportDelete.as_view(), name='support-delete'),


    path('schedule/week/', views.CalendarView.as_view(template_name="schedule/week.html"), name="this-week"),
    path('schedule/week/<int:year>-W<int:week>/', views.CalendarView.as_view(template_name="schedule/week.html"), name="any-week"),
    path('beamtime/', ajax_views.FetchBeamtime.as_view(), name='beamtime-json'),
    path('downtime/', ajax_views.FetchDowntime.as_view(), name='downtime-json'),

]
