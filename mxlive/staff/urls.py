from django.conf.urls import patterns
from lims.forms import ConfirmDeleteForm, LimsBasicForm, ProjectForm, NewUserForm
from lims.models import *  # @UnusedWildImport
from staff.models import UserList, Runlist, Adaptor
from .forms import *  # @UnusedWildImport
import os

# Define url meta data for object lists detail pages
# the url patterns will be dynamically generated from this dictionary
# supported parameters and their defaults:
# 'list': True, 'detail': True, 'edit': False, 'delete': False, 'add': False, 'close': True, 'list_modal_edit': False, 'modal_upload': False,
# 'list_delete_inline': False, 'list_add': False, 'list_link': True,'model', 'form', 'list_add': True, 'list_link': True, 'list_modal': False
# 'list_template': 'objlist/generic_list.html','form_template': 'objforms/form_base.html'
_URL_META = {
    'shipping': {
        'shipment': {'model': Shipment},
        'dewar': {'model': Dewar, 'list_template': 'staff/lists/dewar_list.html'},
        'container': {'model': Container},
    },
    'samples': {
        'crystal': {'model': Crystal, 'list': False},
    },
    'experiment': {
        'request': {'model': Experiment},
        'dataset': {'model': Data, 'list_template': 'staff/lists/dataset_full_list.html'},
        'report': {'model': Result},
        'scan': {'model': ScanResult},
    },
    '': {
        'feedback': {'model': Feedback, 'template': 'users/feedback_item.html', 'list_link': False, 'list_modal': True},
        'runlist': {
            'model': Runlist,
            'form': RunlistForm,
            'template': 'staff/entries/runlist.html',
            'list_add': False,
            'add': True,
            'edit': True,
            'delete': True,
            'delete_form': LimsBasicForm,
            'staff_comments': False,
            'runlist_comments': True,
            'list_template': 'staff/lists/runlist_list.html'
        },
        'userlist': {
            'model': UserList,
            'form': UserListForm,
            'list_link': False,
            'list_modal_edit': True,
            'list_delete_inline': True,
            'comments': False,
            'edit': True
        },
        'link': {
            'model': Link,
            'form': LinkForm,
            'list_template': 'staff/lists/link_object_list.html',
            'detail': False,
            'list_link': False,
            'list_modal_edit': True,
            'list_delete_inline': True,
            'delete_form': LimsBasicForm,
            'list_add': True,
            'add': True,
            'edit': True,
            'delete': True,
            'form_template': 'objforms/form_full.html',
            'modal_upload': True
        },
    },
}

_dynamic_patterns = []
for section, subsection in _URL_META.items():
    for key, params in subsection.items():
        if section:
            base_url = '^%s/%s' % (section, key)
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
                                   'template': params.get('template', 'users/entries/%s.html' % params.get(
                                       'model').__name__.lower())},
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
                 'staff-comments-%s-add' % params.get('model').__name__.lower()))

            # Special Staff Cases
urlpatterns = patterns(
    'mxlive.staff.views',
    (r'^$', 'staff_home', {}, 'staff-home'),
    (r'^profile/edit/(?P<id>\d+)/$', 'edit_profile',
     {'form': ProjectForm, 'template': 'objforms/form_base.html'}, 'staff-profile-edit'),
    (r'^users/new/$', 'create_project', {'form': NewUserForm, 'template': 'objforms/form_base.html'},
     'staff-create-profile'),

    # Dewars
    (r'^shipping/dewar/receive/(?P<id>\d+)$', 'receive_shipment',
     {'model': Dewar, 'form': DewarReceiveForm, 'template': 'objforms/form_base.html',
      'action': 'receive'}, 'staff-dewar-receive'),

    # Experiments
    (r'^experiment/crystal/action/$', 'object_status', {'model': Crystal}, 'staff-crystal-status'),
    (r'^experiment/dataset/action/$', 'object_status', {'model': Data}, 'staff-dataset-status'),
    (r'^experiment/(?P<id>\d+)/review/$', 'staff_action_object',
     {'model': Experiment, 'form': LimsBasicForm, 'template': 'objforms/form_base.html',
      'action': 'review'}, 'staff-experiment-complete'),

    # Runlists
    (
        r'^runlist/(?P<runlist_id>\d+)/container/basic/(?P<obj_id>\d+)/$', 'container_basic_object_list',
        {'model': Container, 'template': 'staff/lists/basic_container_list.html'},
        'staff-container-basic-list'
    ),
    (
        r'^runlist/(?P<runlist_id>\d+)/adaptor/basic/$', 'adaptor_basic_object_list',
        {'model': Adaptor, 'template': 'staff/lists/basic_adaptor_list.html'},
        'staff-adaptor-basic-list'
    ),
    (r'^runlist/(?P<runlist_id>\d+)/experiment/basic/$', 'experiment_basic_object_list',
     {'model': Experiment, 'template': 'staff/lists/basic_experiment_list.html'},
     'staff-experiment-basic-list'),
    (r'^runlist/(?P<runlist_id>\d+)/project/basic/$', 'project_basic_object_list',
     {'model': Project, 'template': 'staff/lists/basic_project_list.html'},
     'staff-project-basic-list'),
    (r'^runlist/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/experiment/(?P<obj_id>\d+)/$',
     'add_existing_object', {'destination': Runlist, 'obj': Experiment},
     'staff-runlist-add-experiment'),
    (r'^runlist/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/project/(?P<obj_id>\d+)/$',
     'add_existing_object', {'destination': Runlist, 'obj': Project}, 'staff-runlist-add-project'),
    (r'^runlist/(?P<dest_id>\d+)/widget/.*/container/(?P<obj_id>\d+)/loc/(?P<loc_id>\w{1,2})/$',
     'add_existing_object', {'destination': Runlist, 'obj': Container},
     'staff-runlist-add-container'),
    (r'^runlist/(?P<id>\d+)/load/$', 'staff_action_object',
     {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html',
      'action': 'load'}, 'staff-runlist-load'),
    (r'^runlist/(?P<id>\d+)/unload/$', 'staff_action_object',
     {'model': Runlist, 'form': RunlistEmptyForm, 'template': 'objforms/form_base.html',
      'action': 'unload'}, 'staff-runlist-complete'),
    (r'^runlist/(?P<id>\d+)/history/$', 'object_history', {'model': Runlist},
     'staff-runlist-history'),
)

# Dynamic patterns here
urlpatterns += patterns('mxlive.lims.views', *_dynamic_patterns)

# Special LIMS Cases
urlpatterns += patterns(
    'mxlive.lims.views',

    (
        r'^users/$', 'object_list', {
            'model': Project,
            'template': 'staff/lists/profiles.html',
            'can_add': params.get('list_add', True),
            # 'link': params.get('list_link', True),
            # 'modal_link': params.get('list_modal', False),
        }, 'staff-get-profiles'),

    # Shipments
    (
        r'^shipping/shipment/(?P<id>\d+)/return/$', 'action_object', {
            'model': Shipment, 'form': ShipmentReturnForm, 'template': 'objforms/form_base.html',
            'action': 'return'}, 'staff-shipment-return'),
    (
        r'^shipping/shipment/(?P<id>\d+)/label/$', 'shipment_pdf', {
            'model': Shipment, 'format': 'return_label'
        }, 'staff-shipment-label'),
    (
        r'^shipping/project/(?P<id>\d+)/form/$', 'shipment_pdf', {
            'model': Project, 'format': 'return_label'
        }, 'staff-shipment-form'),
    (
        r'^shipping/shipment/(?P<id>\d+)/protocol/$', 'shipment_pdf', {
            'model': Shipment, 'format': 'protocol'
        }, 'staff-shipment-protocol'),
    (
        r'^shipping/shipment/(?P<id>\d+)/progress/$', 'object_detail', {
            'model': Shipment, 'template': 'users/entries/progress_report.html'
        }, 'lims-shipment-progress'),

    # Runlists
    (r'^runlist/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/remove/$', 'remove_object',
     {'source': Runlist, 'obj': Container}, 'staff-runlist-remove-container'),
    (r'^runlist/(?P<id>\d+)/protocol/$', 'shipment_pdf', {'model': Runlist, 'format': 'runlist'},
     'staff-runlist-pdf'),
    (r'^runlist/(?P<id>\d+)/staff_comments/add/$', 'staff_comments',
     {'model': Runlist, 'form': RunlistCommentsForm, }, 'staff-comments-runlist-add'),
)

urlpatterns += patterns(
    'django.shortcuts',
    (r'^experiment/$', 'redirect', {'url': '/staff/experiment/request/'}),
    (r'^samples/$', 'redirect', {'url': '/staff/samples/crystal/'}),
)

urlpatterns += patterns(
    '',
    (r'^link/media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': os.path.join('media/')}),
)

