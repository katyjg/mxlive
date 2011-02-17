from django.conf.urls.defaults import patterns, url
from django.conf import settings
from imm.lims.models import *
from imm.lims.forms import *
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
        'cocktail': {'model': Cocktail, 'form': CocktailForm, 'list_link': False, 'list_modal_edit': True, 'list_delete_inline': True}, 
        'crystalform': {'model': CrystalForm, 'form': CrystalFormForm,'list_link': False, 'list_modal_edit': True, 'list_delete_inline': True},  
    },
    'experiment': {
        'request':  {'model': Experiment, 'form': ExperimentForm},       
        'dataset':  {'model': Data, 'add': False, 'list_link': False, 'list_add': False, 'list_modal': True},       
        'report':   {'model': Result, 'add': False, 'list_add': False},         
    },
}

_dynamic_patterns = []
for section, subsection in _URL_META.items():
    for key, params in subsection.items():
        # Object Lists
        if params.get('list', True):
            _dynamic_patterns.append(
                (r'^%s/%s/$' % (section, key),
                 'object_list', {'model': params.get('model'), 
                                 'template': params.get('list_template', 'objlist/generic_list.html'),
                                 'can_add': params.get('list_add', True), 
                                 'link': params.get('list_link', True),
                                 'modal_link': params.get('list_modal', False),
                                 'modal_edit': params.get('list_modal_edit', False),
                                 'delete_inline': params.get('list_delete_inline', False),
                                 },
                 'lims-%s-list' % params.get('model').__name__.lower()))
        

        # Object Basic Lists
        if params.get('basic_list', True):
            _dynamic_patterns.append(
                (r'^%s/%s/basic/$' % (section, key),
                 'basic_object_list', {'model': params.get('model'), 
                                 'template': params.get('list_template', 'objlist/basic_object_list.html'),
                                 },
                 'lims-%s-basic-list' % params.get('model').__name__.lower()))

        # Object add
        if params.get('add', True):
            _dynamic_patterns.append(
                (r'^%s/%s/new/$' % (section, key),
                 'create_object', {'model': params.get('model'),
                                   'form': params.get('form'),
                                   'template': params.get('form_template', 'objforms/form_base.html')
                                   },
                 'lims-%s-new' % params.get('model').__name__.lower()))

        # Object detail
        if params.get('detail', True):
            _dynamic_patterns.append(
                (r'^%s/%s/(?P<id>\d+)/$' % (section, key),
                 'object_detail', {'model': params.get('model'), 
                                   'template': 'lims/entries/%s.html' % params.get('model').__name__.lower()},
                 'lims-%s-detail' % params.get('model').__name__.lower()))

        # Object edit
        if params.get('edit', True):
            _dynamic_patterns.append(
                (r'^%s/%s/(?P<id>\d+)/edit/$' % (section, key),
                 'edit_object_inline', {'model': params.get('model'),
                                        'form': params.get('form'),
                                        'template': params.get('form_template', 'objforms/form_base.html'),
                                        },
                 'lims-%s-edit' % params.get('model').__name__.lower()))


        # Object delete
        if params.get('delete', True):
            _dynamic_patterns.append(
                (r'^%s/%s/(?P<id>\d+)/delete/$' % (section, key),
                 'delete_object', {'model': params.get('model'),
                                   'form': ConfirmDeleteForm,
                                   'template': params.get('form_template', 'objforms/form_base.html'),
                                   },
                 'lims-%s-delete' % params.get('model').__name__.lower()))

        # Object close
        if params.get('close', True):
            _dynamic_patterns.append(
                (r'^%s/%s/(?P<id>\d+)/close/$' % (section, key),
                 'close_object', {'model': params.get('model'),
                                   'form': ConfirmDeleteForm,
                                   'template': params.get('form_template', 'objforms/form_base.html'),
                                   },
                 'lims-%s-close' % params.get('model').__name__.lower()))

urlpatterns = patterns('imm.lims.views',
    (r'^$', 'show_project', {}, 'project-home'),
    (r'^profile/edit/$', 'edit_profile', {'form': ProjectForm, 'template': 'objforms/form_base.html'}, 'lims-profile-edit'),
    (r'^send/feedback/$', 'create_object', {'model': Feedback, 'form': FeedbackForm, 'template': 'objforms/form_base.html'}, 'lims-feedback-new'),
)

# Dynamic patterns here
urlpatterns += patterns('imm.lims.views', *_dynamic_patterns )

# Special cases
urlpatterns += patterns('imm.lims.views',
    # Shipments
    (r'^shipping/shipment/(?P<id>\d+)/send/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentSendForm, 'template': 'objforms/form_base.html', 'action' : 'send'}, 'lims-shipment-send'),
    (r'^shipping/shipment/(?P<id>\d+)/label/$', 'shipment_pdf', {'model': Shipment, 'format' : 'label' }, 'lims-shipment-label'),
    (r'^shipping/shipment/(?P<id>\d+)/xls/$', 'shipment_xls', {}, 'lims-shipment-xls'),
    (r'^shipping/shipment/upload/$', 'upload_shipment', {'model': Shipment, 'form': ShipmentUploadForm, 'template': 'objforms/form_full.html'}, 'lims-shipment-upload'),
    (r'^shipping/shipment/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-add-dewar'),
    (r'^shipping/shipment/.*/widget/(?P<src_id>\d+)/dewar/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Dewar, 'object':Container}, 'lims-shipment-add-container'),
    (r'^shipping/shipment/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source': Shipment, 'object': Dewar, 'reverse': True}, 'lims-dewar-remove'),
    (r'^shipping/shipment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'remove_object', {'source':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-remove-dewar'),
    
    # Dewars
    (r'^shipping/dewar/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Dewar, 'object':Container, 'reverse':True}, 'lims-dewar-add-container'),
    (r'^shipping/dewar/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source':Dewar, 'object':Container, 'reverse':True}, 'lims-dewar-remove-container'),
    (r'^shipping/dewar/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'remove_object', {'source':Dewar, 'object':Container, 'reverse':True}, 'lims-shipment-remove-container'),

    # Containers
    (r'^shipping/container/(?P<dest_id>\d+)/widget/.*/crystal/(?P<obj_id>\d+)/loc/(?P<loc_id>\w{1,2})/$', 'add_existing_object', {'destination':Container, 'object':Crystal, 'reverse':True}, 'lims-container-add-crystal'),
    (r'^shipping/container/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source':Container, 'object':Crystal, 'reverse':True}, 'lims-container-remove-crystal'),
    
    # Crystals
    (r'^samples/crystal/(?P<id>\d+)/priority/$', 'priority', {'model': Crystal, 'field': 'priority'}, 'lims-crystal-priority'),
    (r'^samples/crystal/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object':Cocktail, 'replace': True}, 'lims-crystal-add-cocktail'),
    (r'^samples/crystal/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystalform/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object': CrystalForm, 'replace':True}, 'lims-crystal-add-crystalform'),
    (r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'remove_object', {'source':Crystal, 'object':Cocktail}, 'lims-crystal-remove-cocktail'),
    (r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'remove_object', {'source':Crystal, 'object':Cocktail}, 'lims-crystal-remove-cocktail'),

    # Requests
    (r'^experiment/request/(?P<id>\d+)/priority/$', 'priority', {'model': Experiment, 'field': 'priority'}, 'lims-experiment-priority'),
    (r'^experiment/request/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-add-crystal'),
    (r'^experiment/experiment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'remove_object', {'source':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-remove-crystal'),

    # Report images
    (r'^experiment/result/(\d+)/shellstats.png$', 'plot_shell_stats', {}, 'lims-plot-shells'),
    (r'^experiment/result/(\d+)/framestats.png$', 'plot_frame_stats', {}, 'lims-plot-frames'),
    (r'^experiment/result/(\d+)/diffstats.png$', 'plot_diff_stats', {}, 'lims-plot-diffs'),
    (r'^experiment/result/(\d+)/stderr.png$', 'plot_error_stats', {}, 'lims-plot-stderr'),
    (r'^experiment/result/(\d+)/profiles.png$', 'plot_profiles_stats', {}, 'lims-plot-profiles'),
    (r'^experiment/result/(\d+)/wilson.png$', 'plot_wilson_stats', {}, 'lims-plot-wilson'),
    (r'^experiment/result/(\d+)/twinning.png$', 'plot_twinning_stats', {}, 'lims-plot-twinning'),
            
)

# redirect the top level pages
urlpatterns += patterns('django.views.generic.simple',
    (r'^shipping/$', 'redirect_to', {'url': '/lims/shipping/shipment/'}),
    (r'^experiment/$', 'redirect_to', {'url': '/lims/experiment/request/'}),
    (r'^samples/$', 'redirect_to', {'url': '/lims/samples/crystal/'}),
)

# Debug options
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join('media/')}),
    )
    
    from django.contrib import databrowse
    urlpatterns += patterns('',
        (r'^browse/(.*)', databrowse.site.root),
    )

    _databrowse_model_list = [
                Project, 
                Carrier,
                Shipment,
                Dewar,
                Container,
                SpaceGroup,
                CrystalForm,
                Cocktail,
                Crystal,
                Experiment,
                Result,
                Data,
                ActivityLog,
                Strategy,
                ScanResult,
                Feedback,
                ]
                
    for mod in _databrowse_model_list:
        databrowse.site.register(mod)

