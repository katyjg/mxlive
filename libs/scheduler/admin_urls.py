from django.conf.urls import patterns, url

from scheduler import views
from scheduler import models
from scheduler import forms

urlpatterns = patterns('',
    # staff calendar urls
    url(r'^admin/$', views.admin_scheduler, name='admin-thisweek'),
    url(r'^admin/(?P<day>\d{4}-\d{2}-\d{2})/$', views.admin_scheduler, name='admin-anyweek'),
    url(r'^staff/$', views.staff_calendar, name='staff-thisweek'),
    url(r'^staff/(?P<day>\d{4}-\d{2}-\d{2})/$', views.staff_calendar, name='staff-anyweek'),
    
    # action urls                   
    url(r'^add-visit/$', 
        views.add_object, {'model': models.Visit, 'form': forms.AdminVisitForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-add-visit'),             
    url(r'^edit-visit/(?P<pk>\d+)/$', 
        views.edit_visit, {'model': models.Visit, 'form': forms.AdminEditForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-edit-visit'),    
    url(r'^delete-visit/(?P<pk>\d+)/send/$', 
        views.delete_object, {'model': models.Visit, 'form': forms.DeleteForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-delete-visit'),    
    url(r'^add-oncall/$',
        views.add_object, {'model': models.OnCall, 'form': forms.AdminOnCallForm, 'template': 'scheduler/form_full.html'},
        name='bl-add-oncall'), 
    url(r'^delete-oncall/(?P<pk>\d+)/$', 
        views.delete_object, {'model': models.OnCall, 'form': forms.DeleteOnCallForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-delete-oncall'), 
    url(r'^get-modes/$', 
        views.add_object, {'model': models.Stat, 'form': forms.AdminStatusForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-add-mode'), 
    url(r'^breakdown/$', 
        views.get_shift_breakdown, {'template': 'scheduler/shift_breakdown.html'},
        name='bl.breakdown'),
    url(r'^breakdown/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})/$', 
        views.get_shift_breakdown, {'template': 'scheduler/shift_breakdown.html'},
        name='bl.breakdown.dates'),
)
