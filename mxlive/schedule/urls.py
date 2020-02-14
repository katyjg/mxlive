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

    path('schedule/week/', views.CalendarView.as_view(template_name="schedule/week.html"), name="this-week"),
    path('schedule/week/<int:year>-W<int:week>/', views.CalendarView.as_view(template_name="schedule/week.html"), name="any-week"),
    path('beamtime/', ajax_views.FetchBeamtime.as_view(), name='beamtime-json'),

    # path('schedule/template/year/', ajax_views.YearTemplate.as_view(), name="year-template-api"),
    # path('schedule/template/month/', ajax_views.MonthTemplate.as_view(), name="month-template-api"),
    # path('schedule/template/week/', ajax_views.WeekTemplate.as_view(), name="week-template-api"),
    # path('schedule/template/cycle/', ajax_views.CycleTemplate.as_view(), name="cycle-template-api"),
]
