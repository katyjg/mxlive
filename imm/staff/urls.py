from django.conf.urls.defaults import patterns, url
from django.contrib.auth.models import User
from django import forms
from django.conf import settings

import os

from imm.lims.models import *
from imm.staff.models import Runlist, Link
from imm.lims.forms import ExperimentForm, ConfirmDeleteForm, LimsBasicForm
from imm.staff.forms import *

# Define url meta data for object lists detail pages
# the url patterns will be dynamically generated from this dictionary
# supported parameters and their defaults:
#'list': True, 'detail': True, 'edit': False, 'delete': False, 'add': False, 'close': True, 'list_modal_edit': False, 'modal_upload': False,
#'list_delete_inline': False, 'list_add': False, 'list_link': True,'model', 'form', 'list_add': True, 'list_link': True, 'list_modal': False
#'list_template': 'objlist/generic_list.html','form_template': 'objforms/form_base.html'
_URL_META = {
    'shipping': {
        'shipment': {'model': Shipment},        
        'dewar':    {'model': Dewar, 'list_template': 'staff/lists/dewar_list.html'},        
        'container':{'model': Container},        
    },
    'samples': {
        'crystal':  {'model': Crystal, 'list': False},
    },
    'experiment': {
        'request':  {'model': Experiment},       
        'dataset':  {'model': Data, 'list_template': 'staff/lists/dataset_list.html'},       
        'report':   {'model': Result},     
        'scan':     {'model': ScanResult},    
    },
    '': {
        'feedback': {'model': Feedback, 'template': 'lims/feedback_item.html', 'list_link': False, 'list_modal': True},
        'runlist': {'model': Runlist, 'form': RunlistForm, 'template': 'staff/entries/runlist.html', 
                    'list_add': False, 'add': True, 'edit': True, 'delete': True, 'delete_form': LimsBasicForm,
                    'staff_comments': False, 'runlist_comments': True, 'list_template': 'staff/lists/runlist_list.html'},
        'link': {'model': Link, 'form': LinkForm, 'list_template': 'staff/lists/link_object_list.html', 
                 'detail': False, 'list_link': False, 'list_modal_edit': True, 'list_delete_inline': True, 'delete_form': LimsBasicForm,
                 'list_add': True, 'add': True, 'edit': True, 'delete': True, 'form_template': 'objforms/form_full.html', 'modal_upload': True},
    },
}

_dynamic_patterns = []
for section, subsection in _URL_META.items():
    for key, params in subsection.items():
        if section:
            base_url = '^%s/%s' % ( section, key)
        else:
            base_url = '^%s' % (key)

        # Object Lists
        if params.get('list', True):
            _dynamic_patterns.append(
                (r'%s/$' % base_url,
                 'object_list', {'model': params.get('model'), 
                                 'template': params.get('list_template', 'objlist/generic_list.html'),
                                 'can_add': params.get('list_add', False), 
                                 'link': params.get('list_link', True),
                                 'modal_link': params.get('list_modal', False),
                                 'modal_edit': params.get('list_modal_edit', False),
                                 'delete_inline': params.get('list_delete_inline', False),
                                 'modal_upload': params.get('modal_upload', False),
                                 },
                 'staff-%s-list' % params.get('model').__name__.lower()))

        # Object detail
        if params.get('detail', True):
            _dynamic_patterns.append(
                (r'%s/(?P<id>\d+)/$' % (base_url),
                 'object_detail', {'model': params.get('model'), 
                                   'template': params.get('template','lims/entries/%s.html' % params.get('model').__name__.lower())},
                 'staff-%s-detail' % params.get('model').__name__.lower()))

        # Object add
        if params.get('add', False):
            _dynamic_patterns.append(
                (r'%s/new/$' % (base_url),
                 'create_object', {'model': params.get('model'),
                                   'form': params.get('form'),
                                   'template': params.get('form_template', 'objforms/form_base.html'),
                                   'modal_upload': params.get('modal_upload', False)
                                   },
                 'staff-%s-new' % params.get('model').__name__.lower()))

        # Object edit
        if params.get('edit', False):
            _dynamic_patterns.append(
                (r'%s/(?P<id>\d+)/edit/$' % (base_url),
                 'edit_object_inline', {'model': params.get('model'),
                                        'form': params.get('form'),
                                        'template': params.get('form_template', 'objforms/form_base.html'),
                                        'modal_upload': params.get('modal_upload', False)
                                        },
                 'staff-%s-edit' % params.get('model').__name__.lower()))


        # Object delete
        if params.get('delete', False):
            _dynamic_patterns.append(
                (r'%s/(?P<id>\d+)/delete/$' % (base_url),
                 'delete_object', {'model': params.get('model'),
                                   'form': params.get('delete_form', ConfirmDeleteForm),
                                   'template': 'objforms/form_base.html',
                                   },
                 'staff-%s-delete' % params.get('model').__name__.lower()))

        # Add Staff Comments
        if params.get('staff_comments', True):
            _dynamic_patterns.append(
                (r'%s/(?P<id>\d+)/staff_comments/add/$' % (base_url),
                 'staff_comments', {'model': params.get('model'),
                                    'form': StaffCommentsForm,
                                   },
                 'staff-comments-%s-add'% params.get('model').__name__.lower()))        

        # Add Staff Comments
        if params.get('staff_comments', True):
            _dynamic_patterns.append(
                (r'%s/(?P<id>\d+)/staff_comments/add/$' % (base_url),
                 'staff_comments', {'model': params.get('model'),
                                    'form': StaffCommentsForm,
                                   },
                 'staff-comments-%s-add'% params.get('model').__name__.lower()))    

#Special Staff Cases
urlpatterns = patterns('imm.staff.views',
    (r'^$', 'staff_home', {}, 'staff-home'),

    # Dewars 
    (r'^shipping/dewar/receive/(?P<id>\d+)$', 'receive_shipment', {'model': Dewar, 'form': DewarReceiveForm, 'template': 'objforms/form_base.html', 'action': 'receive'}, 'staff-dewar-receive'),

    # Experiments
    (r'^experiment/crystal/action/$', 'object_status', {'model': Crystal}, 'staff-crystal-status'),
    (r'^experiment/dataset/action/$', 'object_status', {'model': Data}, 'staff-dataset-status'),
    (r'^experiment/(?P<id>\d+)/review/$', 'staff_action_object', {'model': Experiment, 'form': LimsBasicForm, 'template': 'objforms/form_base.html', 'action': 'review'}, 'staff-experiment-complete'),

    # Runlists
    (r'^runlist/(?P<runlist_id>\d+)/container/basic/(?P<exp_id>\d+)/$', 'container_basic_object_list', {'model':Container, 'template': 'staff/lists/basic_container_list.html'}, 'staff-container-basic-list'),
    (r'^runlist/(?P<runlist_id>\d+)/experiment/basic/$', 'experiment_basic_object_list', {'model':Experiment, 'template': 'staff/lists/basic_experiment_list.html'}, 'staff-experiment-basic-list'),
    (r'^runlist/(?P<runlist_id>\d+)/project/basic/$', 'project_basic_object_list', {'model':Project, 'template': 'staff/lists/basic_project_list.html'}, 'staff-project-basic-list'),   
    (r'^runlist/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/experiment/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Runlist, 'object':Experiment }, 'staff-runlist-add-experiment'),
    (r'^runlist/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/project/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Runlist, 'object':Project }, 'staff-runlist-add-project'),
    (r'^runlist/(?P<dest_id>\d+)/widget/.*/container/(?P<obj_id>\d+)/loc/(?P<loc_id>\w{1,2})/$', 'add_existing_object', {'destination':Runlist, 'object':Container }, 'staff-runlist-add-container'),
    (r'^runlist/(?P<id>\d+)/load/$', 'staff_action_object', {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html', 'action' : 'load'}, 'staff-runlist-load'),
    (r'^runlist/(?P<id>\d+)/unload/$', 'staff_action_object', {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html', 'action' : 'unload'}, 'staff-runlist-complete'),
    (r'^runlist/(?P<id>\d+)/history/$', 'object_history', {'model': Runlist}, 'staff-runlist-history'),
)

# Dynamic patterns here
urlpatterns += patterns('imm.lims.views', *_dynamic_patterns )

#Special LIMS Cases
urlpatterns += patterns('imm.lims.views',

    # Shipments
    (r'^shipping/shipment/(?P<id>\d+)/return/$', 'action_object', {'model': Shipment, 'form': ShipmentReturnForm, 'template': 'objforms/form_base.html', 'action' : 'return'}, 'staff-shipment-return'),
    (r'^shipping/shipment/(?P<id>\d+)/label/$', 'shipment_pdf', {'model': Shipment, 'format' : 'return_label' }, 'staff-shipment-label'),    
    (r'^shipping/shipment/(?P<id>\d+)/protocol/$', 'shipment_pdf', {'model': Shipment, 'format' : 'protocol' }, 'staff-shipment-protocol'),    
    (r'^shipping/shipment/(?P<id>\d+)/progress/$', 'object_detail', {'model': Shipment, 'template' : 'lims/entries/progress_report.html' }, 'lims-shipment-progress'),

    # Runlists
    (r'^runlist/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source':Runlist, 'object':Container }, 'staff-runlist-remove-container'),
    (r'^runlist/(?P<id>\d+)/protocol/$', 'shipment_pdf', {'model': Runlist, 'format' : 'runlist' }, 'staff-runlist-pdf'),
    (r'^runlist/(?P<id>\d+)/staff_comments/add/$', 'staff_comments', {'model': Runlist, 'form': RunlistCommentsForm,}, 'staff-comments-runlist-add'),    
    
    # Report images
    (r'^experiment/report/(\d+)/shell.png$', 'plot_shell_stats', {}, 'staff-plot-shells'),
    (r'^experiment/report/(\d+)/frame.png$', 'plot_frame_stats', {}, 'staff-plot-frames'),
    (r'^experiment/report/(\d+)/diff.png$', 'plot_diff_stats', {}, 'staff-plot-diffs'),
    (r'^experiment/report/(\d+)/stderr.png$', 'plot_error_stats', {}, 'staff-plot-stderr'),
    (r'^experiment/report/(\d+)/profiles.png$', 'plot_profiles_stats', {}, 'staff-plot-profiles'),
    (r'^experiment/report/(\d+)/wilson.png$', 'plot_wilson_stats', {}, 'staff-plot-wilson'),
    (r'^experiment/report/(\d+)/twinning.png$', 'plot_twinning_stats', {}, 'staff-plot-twinning'),
    (r'^experiment/report/(\d+)/exposure.png$', 'plot_exposure_analysis', {}, 'staff-plot-exposure'),
    (r'^experiment/report/(\d+)/overlap.png$', 'plot_overlap_analysis', {}, 'staff-plot-overlap'),
    (r'^experiment/report/(\d+)/quality.png$', 'plot_pred_quality', {}, 'staff-plot-quality'),
    (r'^experiment/report/(\d+)/wedge.png$', 'plot_wedge_analysis', {}, 'staff-plot-wedge'),
    (r'^experiment/request/(?P<id>\d+)/progress/$', 'object_detail', {'model': Experiment, 'template' : 'lims/entries/progress_report.html' }, 'lims-experiment-progress'),

    
    # Scan images
    (r'^experiment/scan/(\d+)/xrfscan.png$', 'plot_xrf_scan', {}, 'staff-plot-xrf'),
    (r'^experiment/scan/(\d+)/xanesscan.png$', 'plot_xanes_scan', {}, 'staff-plot-xanes'),
)

urlpatterns += patterns('django.views.generic.simple',
    (r'^experiment/$', 'redirect_to', {'url': '/staff/experiment/request/'}),
    (r'^samples/$', 'redirect_to', {'url': '/staff/samples/crystal/'}),
)

urlpatterns += patterns('',
    (r'^link/media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join('media/')}),
)
