import django
from django.conf.urls import url
from django.conf import settings
from models import *
from forms import *
from views import *
import os

# Define url meta data for object lists, add, edit, delete, and detail pages
# the url patterns will be dynamically generated from this dictionary
# supported parameters and their defaults:
#'list': True, 'detail': True, 'edit': True, 'delete': True, 'add': True, 'close': True, 'list_modal_edit': False, 'basic_list': True, 
#'list_delete_inline': False, 'list_add': True, 'list_link': True,'model', 'form', 'list_add': True, 'list_link': True, 'list_modal': False
#'list_template': 'objlist/generic_list.html','form_template': 'objforms/form_base.html'
_URL_META = {
    'shipping': {
        'shipment': {'model': Shipment, 'form': ShipmentForm},        
        'dewar':    {'model': Dewar, 'form': DewarForm},        
        'container':{'model': Container, 'form': ContainerForm},        
    },
    'samples': {
        'crystal':  {'model': Crystal, 'form': SampleForm},
        'cocktail': {'model': Cocktail, 'form': CocktailForm, 'list_link': False, 'list_modal_edit': True, 'list_delete_inline': True, 'comments': False}, 
        'crystalform': {'model': CrystalForm, 'form': CrystalFormForm,'list_link': False, 'list_modal_edit': True, 'list_delete_inline': True, 'comments': False},  
    },
    'experiment': {
        'request':  {'model': Experiment, 'form': ExperimentForm},       
        'dataset':  {'model': Data, 'add': False, 'list_link': False, 'list_add': False, 'list_modal': True, 'comments': False, 'delete': False},       
        'report':   {'model': Result, 'add': False, 'list_add': False, 'comments': False},   
        'scan':     {'model': ScanResult, 'add': False, 'list_add': False},      
    },
}

_dynamic_patterns = []
for section, subsection in _URL_META.items():
    for key, params in subsection.items():
        # Object Lists
        if params.get('list', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/$' % (section, key),
                 object_list, {'model': params.get('model'),
                                 'template': params.get('list_template', 'objlist/generic_list.html'),
                                 'can_add': params.get('list_add', True), 
                                 'link': params.get('list_link', True),
                                 'modal_link': params.get('list_modal', False),
                                 'modal_edit': params.get('list_modal_edit', False),
                                 'delete_inline': params.get('list_delete_inline', False),
                                 },
                 'users-%s-list' % params.get('model').__name__.lower()))
        

        # Object Basic Lists
        if params.get('basic_list', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/basic/$' % (section, key),
                 basic_object_list, {'model': params.get('model'),
                                 'template': params.get('list_template', 'objlist/basic_object_list.html'),
                                 },
                 'users-%s-basic-list' % params.get('model').__name__.lower()))

        # Object add
        if params.get('add', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/new/$' % (section, key),
                 create_object, {'model': params.get('model'),
                                   'form': params.get('form'),
                                   'template': params.get('form_template', 'objforms/form_base.html')
                                   },
                 'users-%s-new' % params.get('model').__name__.lower()))

        # Object detail
        if params.get('detail', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/(?P<id>\d+)/$' % (section, key),
                 object_detail, {'model': params.get('model'),
                                   'template': 'users/entries/%s.html' % params.get('model').__name__.lower()},
                 'users-%s-detail' % params.get('model').__name__.lower()))

        # Object edit
        if params.get('edit', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/(?P<id>\d+)/edit/$' % (section, key),
                 edit_object_inline, {'model': params.get('model'),
                                        'form': params.get('form'),
                                        'template': params.get('form_template', 'objforms/form_base.html'),
                                        },
                 'users-%s-edit' % params.get('model').__name__.lower()))


        # Object delete
        if params.get('delete', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/(?P<id>\d+)/delete/$' % (section, key),
                 delete_object, {'model': params.get('model'),
                                   'form': params.get('delete_form', ConfirmDeleteForm),
                                   'template': params.get('form_template', 'objforms/form_base.html'),
                                   },
                 'users-%s-delete' % params.get('model').__name__.lower()))

        # Object close
        if params.get('close', True):
            _dynamic_patterns.append(
                url(r'^%s/%s/(?P<id>\d+)/close/$' % (section, key),
                 action_object, {'model': params.get('model'),
                                   'form': LimsBasicForm,
                                   'template': params.get('form_template', 'objforms/form_base.html'),
                                   'action': 'archive',
                                   },
                 'users-%s-close' % params.get('model').__name__.lower()))

        # Add Comments 
        if params.get('comments', True):
            _dynamic_patterns.append(
                url(r'%s/%s/(?P<id>\d+)/comments/add/$' % (section, key),
                 staff_comments, {'model': params.get('model'),
                                    'form': CommentsForm,
                                    'user': 'user',
                                   },
                 'users-comments-%s-add'% params.get('model').__name__.lower()))        

urlpatterns = [
    url(r'^$', show_project, {}, 'project-home'),
    url(r'^profile/edit/$', edit_profile, {'form': ProjectForm, 'template': 'objforms/form_base.html'}, 'users-profile-edit'),
    url(r'^profile/edit/(?P<id>\d+)/$', edit_profile, {'form': ProjectForm, 'template': 'objforms/form_base.html'}, 'users-profile-edit-send'),
    url(r'^send/feedback/$', create_object, {'model': Feedback, 'form': FeedbackForm, 'template': 'objforms/form_base.html'}, 'users-feedback-new'),
]

# Dynamic patterns here
urlpatterns += _dynamic_patterns

# Special cases
urlpatterns += [
    # Shipments
    url(r'^shipping/shipment/(?P<id>\d+)/send/$', action_object, {'model': Shipment, 'form': ShipmentSendForm, 'template': 'objforms/form_base.html', 'action' : 'send'}, 'users-shipment-send'),
    url(r'^shipping/shipment/(?P<id>\d+)/label/$', shipment_pdf, {'model': Shipment, 'format' : 'label' }, 'users-shipment-label'),
    url(r'^shipping/shipment/(?P<id>\d+)/xls/$', shipment_xls, {}, 'users-shipment-xls'),
    url(r'^shipping/shipment/upload/$', upload_shipment, {'model': Shipment, 'form': ShipmentUploadForm, 'template': 'objforms/form_full.html'}, 'users-shipment-upload'),
    url(r'^shipping/shipment/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/$', add_existing_object, {'destination':Shipment, 'obj':Dewar, 'reverse':True}, 'users-shipment-add-dewar'),
    url(r'^shipping/shipment/.*/widget/(?P<src_id>\d+)/dewar/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', add_existing_object, {'destination':Dewar, 'obj':Container}, 'users-shipment-add-container'),
    url(r'^shipping/shipment/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/remove/$', remove_object, {'source': Shipment, 'obj': Dewar, 'reverse': True}, 'users-dewar-remove'),
    url(r'^shipping/shipment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/dewar/(?P<obj_id>\d+)/$', remove_object, {'source':Shipment, 'obj':Dewar, 'reverse':True}, 'users-shipment-remove-dewar'),
    url(r'^shipping/shipment/(?P<id>\d+)/progress/$', object_detail, {'model': Shipment, 'template' : 'users/entries/progress_report.html' }, 'users-shipment-progress'),
    url(r'^shipping/shipment/(?P<id>\d+)/component/$', create_object, {'model': Component, 'form': ComponentForm, 'template': 'objforms/form_base.html'}, 'users-component-add'),
    url(r'^shipping/shipment/component/(?P<id>\d+)/edit/$', edit_object_inline, {'model': Component, 'form': ComponentForm, 'template': 'objforms/form_base.html'}, 'users-component-edit'),
    url(r'^shipping/shipment/component/(?P<id>\d+)/delete/$', delete_object, {'model': Component, 'form': LimsBasicForm, 'template': 'objforms/form_base.html'}, 'users-component-delete'),
        
    # Dewars
    url(r'^shipping/dewar/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/$', add_existing_object, {'destination':Dewar, 'obj':Container, 'reverse':True}, 'users-dewar-add-container'),
    url(r'^shipping/dewar/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/remove/$', remove_object, {'source':Dewar, 'obj':Container, 'reverse':True}, 'users-dewar-remove-container'),
    url(r'^shipping/dewar/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', remove_object, {'source':Dewar, 'obj':Container, 'reverse':True}, 'users-shipment-remove-container'),

    # Containers
    url(r'^shipping/container/(?P<dest_id>\d+)/widget/.*/crystal/(?P<obj_id>\d+)/loc/(?P<loc_id>\w{1,2})/$', add_existing_object, {'destination':Container, 'obj':Crystal, 'reverse':True}, 'users-container-add-crystal'),
    url(r'^shipping/container/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/remove/$', remove_object, {'source':Container, 'obj':Crystal, 'reverse':True}, 'users-container-remove-crystal'),
    
    # Crystals
    url(r'^samples/crystal/(?P<id>\d+)/priority/$', priority, {'model': Crystal, 'field': 'priority'}, 'users-crystal-priority'),
    url(r'^samples/crystal/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/cocktail/(?P<obj_id>\d+)/$', add_existing_object, {'destination':Crystal, 'obj':Cocktail, 'replace': True}, 'users-crystal-add-cocktail'),
    url(r'^samples/crystal/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystalform/(?P<obj_id>\d+)/$', add_existing_object, {'destination':Crystal, 'obj': CrystalForm, 'replace':True}, 'users-crystal-add-crystalform'),
    url(r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', remove_object, {'source':Crystal, 'obj':Cocktail}, 'users-crystal-remove-cocktail'),
    url(r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', remove_object, {'source':Crystal, 'obj':Cocktail}, 'users-crystal-remove-cocktail'),

    # Requests
    url(r'^experiment/request/(?P<id>\d+)/priority/$', priority, {'model': Experiment, 'field': 'priority'}, 'users-experiment-priority'),
    url(r'^experiment/request/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/$', add_existing_object, {'destination':Experiment, 'obj':Crystal, 'reverse':True}, 'users-experiment-add-crystal'),
    url(r'^experiment/experiment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', remove_object, {'source':Experiment, 'obj':Crystal, 'reverse':True}, 'users-experiment-remove-crystal'),
    url(r'^experiment/request/(?P<id>\d+)/progress/$', object_detail, {'model': Experiment, 'template' : 'users/entries/progress_report.html' }, 'users-experiment-progress'),

    url(r'^experiment/dataset/(?P<id>\d+)/trash/$', action_object, {'model': Data, 'form': LimsBasicForm, 'template': 'objforms/form_base.html', 'action': 'trash', }, 'users-data-trash'),
    url(r'^experiment/report/(?P<id>\d+)/trash/$', action_object, {'model': Result, 'form': LimsBasicForm, 'template': 'objforms/form_base.html', 'action': 'trash', }, 'users-result-trash'),
]

# redirect the top level pages
urlpatterns += [
    url(r'^shipping/$', django.shortcuts.redirect, {'url': '/users/shipping/shipment/'}),
    url(r'^experiment/$', django.shortcuts.redirect, {'url': '/users/experiment/request/'}),
    url(r'^samples/$', django.shortcuts.redirect, {'url': '/users/samples/crystal/'}),
]

# Debug options
if settings.DEBUG:
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', django.views.static.serve, {
            'document_root': os.path.join(os.path.dirname(__file__), 'media/')
        }),
    ]
