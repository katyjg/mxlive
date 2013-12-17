from django.conf.urls.defaults import *

import views
from models import *
from forms import *

urlpatterns = patterns('',
    # staff calendar urls
    url(r'^admin/$', views.admin_scheduler, name='admin-scheduler.thisweek'),
    url(r'^admin/(?P<day>\d{4}-\d{2}-\d{2})/$', views.admin_scheduler, name='admin-scheduler.anyweek'),
    url(r'^staff/$', views.staff_calendar, name='staff-scheduler.thisweek'),
    url(r'^staff/(?P<day>\d{4}-\d{2}-\d{2})/$', views.staff_calendar, name='staff-scheduler.anyweek'),
    
    # action urls                   
    url(r'^add-visit/$', 
        views.add_object, {'model': Visit, 'form': AdminVisitForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-add-visit'),             
    url(r'^edit-visit/(?P<pk>\d+)/$', 
        views.edit_visit, {'model': Visit, 'form': AdminEditForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-edit-visit'),    
    url(r'^delete-visit/(?P<pk>\d+)/send/$', 
        views.delete_object, {'model': Visit, 'form': BasicForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-delete-visit'),    
    url(r'^add-oncall/$',
        views.add_object, {'model': OnCall, 'form': AdminOnCallForm, 'template': 'scheduler/form_full.html'},
        name='bl-add-oncall'), 
    url(r'^delete-oncall/(?P<pk>\d+)/$', 
        views.delete_object, {'model': OnCall, 'form': BasicForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-delete-oncall'), 
    url(r'^get-modes/$', 
        views.add_object, {'model': Stat, 'form': AdminStatusForm, 'template': 'scheduler/form_full.html'}, 
        name='bl-add-mode'), 
    url(r'^breakdown/$', 
        views.get_shift_breakdown, {'template': 'scheduler/shift_breakdown.html'},
        name='bl.breakdown'),
    url(r'^breakdown/(?P<start>\d{4}-\d{2}-\d{2})/(?P<end>\d{4}-\d{2}-\d{2})/$', 
        views.get_shift_breakdown, {'template': 'scheduler/shift_breakdown.html'},
        name='bl.breakdown.dates'),
)
