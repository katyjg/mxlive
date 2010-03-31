from django.conf.urls.defaults import patterns, url
from django.contrib.auth.models import User
from django import forms

from imm.lims.models import Shipment
from imm.lims.models import Dewar
from imm.lims.models import Experiment
from imm.lims.models import Container
from imm.lims.models import Crystal
from imm.lims.models import Cocktail
from imm.lims.models import CrystalForm
from imm.lims.models import Constituent
from imm.lims.models import ExcludeManagerWrapper
from imm.staff.models import Runlist

from imm.lims.forms import ExperimentForm

from imm.staff.forms import ShipmentReceiveForm
from imm.staff.forms import ShipmentReturnForm
from imm.staff.forms import DewarReceiveForm
from imm.staff.forms import DewarForm
from imm.staff.forms import ExperimentSelectForm
from imm.staff.forms import ContainerSelectForm
from imm.staff.forms import RunlistForm
from imm.staff.forms import RunlistEmptyForm
from imm.staff.forms import RunlistAcceptForm

urlpatterns = patterns('',
    (r'^$', 'imm.staff.views.staff_home', {}, 'staff-home'),
    
    (r'^shipping/shipment/$', 'imm.lims.views.object_list', {'model': Shipment, 'template': 'lims/lists/shipping_list.html', 'can_receive': True}, 'staff-shipment-list'),
    (r'^shipping/shipment/receive/$', 'imm.staff.views.receive_shipment', {'model': Dewar, 'form': DewarReceiveForm, 'template': 'lims/forms/shipping_base.html', 'action': 'receive'}, 'staff-shipment-receive-any'),
    (r'^shipping/shipment/(?P<id>\d+)/receive/$', 'imm.lims.views.edit_object_inline', {'model': Shipment, 'form': ShipmentReceiveForm, 'template': 'objforms/form_base.html', 'action' : 'receive'}, 'staff-shipment-receive'),
    (r'^shipping/shipment/(?P<id>\d+)/return/$', 'imm.lims.views.edit_object_inline', {'model': Shipment, 'form': ShipmentReturnForm, 'template': 'objforms/form_base.html', 'action' : 'return'}, 'staff-shipment-return'),
    
    (r'^shipping/dewar/(?P<id>\d+)/edit/$', 'imm.lims.views.edit_object_inline', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'staff-dewar-edit'),
    
    (r'^samples/crystal/$', 'imm.lims.views.object_list', {'model': Crystal, 'template': 'lims/lists/samples_list.html'}, 'staff-crystal-list'),
    (r'^samples/crystal/(?P<id>\d+)/up/$', 'imm.lims.views.change_priority', {'model': Crystal, 'action': 'up', 'field': 'staff_priority'}, 'staff-crystal-up'),
    (r'^samples/crystal/(?P<id>\d+)/down/$', 'imm.lims.views.change_priority', {'model': Crystal, 'action': 'down', 'field': 'staff_priority'}, 'staff-crystal-down'),
    
    (r'^experiment/request/$', 'imm.lims.views.object_list', {'model': Experiment, 'template': 'lims/lists/experiment_list.html'}, 'staff-experiment-list'),
    
    (r'^runlist/$', 'imm.lims.views.object_list', {'model': Runlist, 'template': 'staff/lists/runlist_list.html', 'can_add': True, 'can_prioritize': True}, 'staff-runlist-list'),
    (r'^runlist/new/$', 'imm.staff.views.runlist_object_list', {'model': Experiment, 'form': ExperimentSelectForm, 'template': 'staff/lists/runlist_list.html', 'can_prioritize': True, 'link': False, 'redirect': 'staff-runlist-new-step2', 'instructions': 'Prioritize and select some Experiments.'}, 'staff-runlist-new'),
    (r'^runlist/new/step2/$', 'imm.staff.views.runlist_object_list', {'model': Container, 'form': ContainerSelectForm, 'parent_model': Experiment, 'link_field': 'crystal', 'template': 'staff/lists/runlist_list.html', 'link': False, 'redirect': 'staff-runlist-new-step3', 'instructions': 'Select some Containers.'}, 'staff-runlist-new-step2'),
    (r'^runlist/new/step3/$', 'imm.staff.views.runlist_create_object', {'model': Runlist, 'form': RunlistForm }, 'staff-runlist-new-step3'),
    (r'^runlist/new/(?P<id>\d+)/up/$', 'imm.lims.views.change_priority', {'model': Experiment, 'action': 'up', 'field': 'staff_priority'}, 'staff-experiment-up'),
    (r'^runlist/new/(?P<id>\d+)/down/$', 'imm.lims.views.change_priority', {'model': Experiment, 'action': 'down', 'field': 'staff_priority'}, 'staff-experiment-down'),
    (r'^runlist/(?P<id>\d+)/$', 'imm.lims.views.object_detail', {'model': Runlist, 'template': 'staff/entries/runlist.html'}, 'staff-runlist-detail'),
    (r'^runlist/(?P<id>\d+)/up/$', 'imm.lims.views.change_priority', {'model': Runlist, 'action': 'up', 'field': 'priority'}, 'staff-runlist-up'),
    (r'^runlist/(?P<id>\d+)/down/$', 'imm.lims.views.change_priority', {'model': Runlist, 'action': 'down', 'field': 'priority'}, 'staff-runlist-down'),
    (r'^runlist/(?P<id>\d+)/delete/$', 'imm.lims.views.delete_object', {'model': Runlist, 'redirect' : 'staff-runlist-list'}, 'staff-runlist-delete'),
    (r'^runlist/(?P<id>\d+)/edit/$', 'imm.lims.views.edit_object_inline', {'model': Runlist, 'form': RunlistForm, 'template': 'objforms/form_base.html'}, 'staff-runlist-edit'),
    (r'^runlist/(?P<id>\d+)/load/$', 'imm.lims.views.edit_object_inline', {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html', 'action' : 'load'}, 'staff-runlist-load'),
    (r'^runlist/(?P<id>\d+)/unload/$', 'imm.lims.views.edit_object_inline', {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html', 'action' : 'unload'}, 'staff-runlist-complete'),
    (r'^runlist/(?P<id>\d+)/accept/$', 'imm.lims.views.edit_object_inline', {'model': Runlist, 'form': RunlistAcceptForm, 'template': 'objforms/form_base.html', 'action' : 'accept'}, 'staff-runlist-accept'),
    (r'^runlist/(?P<id>\d+)/reject/$', 'imm.lims.views.edit_object_inline', {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html', 'action' : 'reject'}, 'staff-runlist-reject'),
)