from django.conf.urls.defaults import patterns, url
from django.conf import settings
from imm.lims.models import *
from imm.lims.forms import *
import os

urlpatterns = patterns('imm.lims.views',
    (r'^$', 'show_project', {}, 'project-home'),
    (r'^profile/edit/$', 'edit_profile', {'form': ProjectForm, 'template': 'objforms/form_base.html'}, 'lims-profile-edit'),
    (r'^send/feedback/$', 'create_object', {'model': Feedback, 'form': FeedbackForm, 'template': 'objforms/form_base.html'}, 'lims-feedback'),

    #SHIPMENTS##############
    (r'^shipping/shipment/$', 'object_list', {'model': Shipment, 'template': 'objlist/generic_list.html', 'can_add': True, 'link': True }, 'lims-shipment-list'),
    (r'^shipping/shipment/(?P<id>\d+)/$', 'object_detail', {'model': Shipment, 'template': 'lims/entries/shipment.html'}, 'lims-shipment-detail'),
    (r'^shipping/shipment/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-edit'),
    (r'^shipping/shipment/(?P<id>\d+)/send/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentSendForm, 'template': 'objforms/form_base.html', 'action' : 'send'}, 'lims-shipment-send'),
    (r'^shipping/shipment/(?P<id>\d+)/new/$', 'add_new_object', {'model': Dewar, 'form': DewarForm, 'field':'shipment'}, 'lims-shipment-new-dewar'),
    (r'^shipping/shipment/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Dewar, 'parent_model': Shipment, 'field':'shipment'}, 'lims-shipment-add-dewar'), 
    (r'^shipping/shipment/(?P<id>\d+)/delete/$', 'delete_object', {'model': Shipment, 'form': ConfirmDeleteForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-delete'),
    (r'^shipping/shipment/(?P<id>\d+)/close/$', 'close_object', {'model' : Shipment, 'form': ConfirmDeleteForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-close'),
    #(r'^shipping/shipment/(?P<id>\d+)/pdf/$', 'shipment_pdf', {'format' : 'pdf' }, 'lims-shipment-pdf'),
    (r'^shipping/shipment/(?P<id>\d+)/label/$', 'shipment_pdf', {'format' : 'label' }, 'lims-shipment-label'),
    (r'^shipping/shipment/(?P<id>\d+)/xls/$', 'shipment_xls', {}, 'lims-shipment-xls'),
    (r'^shipping/shipment/new/$', 'create_object', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-new'),
    (r'^shipping/shipment/upload/$', 'upload_shipment', {'model': Shipment, 'form': ShipmentUploadForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-upload'),
    (r'^shipping/shipment/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-add-dewar'),
    (r'^shipping/shipment/.*/widget/(?P<src_id>\d+)/dewar/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Dewar, 'object':Container}, 'lims-shipment-add-container'),

    #####################
    (r'^shipping/dewar/basic/$', 'unassigned_object_list', {'model': Dewar, 'related_field': 'shipment', 'template': 'objlist/basic_object_list.html'}, 'lims-dewar-basic-list'),
    #DEWARS##############
    (r'^shipping/dewar/$', 'object_list', {'model': Dewar, 'template': 'objlist/generic_list.html', 'can_add': True, 'link': True}, 'lims-dewar-list'),
    (r'^shipping/dewar/(?P<id>\d+)/$', 'dewar_object_detail', {'model': Dewar, 'template': 'lims/entries/dewar.html'}, 'lims-dewar-detail'),
    (r'^shipping/dewar/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-edit'),
    (r'^shipping/dewar/(?P<id>\d+)/new/$', 'add_new_object', {'model': Container, 'form': ContainerForm, 'field':'dewar'}, 'lims-dewar-new-container'),
    (r'^shipping/dewar/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Container, 'parent_model': Dewar, 'field':'dewar'}, 'lims-dewar-add-container'),
    (r'^shipping/dewar/new/$', 'create_object', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-new'),
    (r'^shipping/dewar/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Dewar, 'object':Container, 'reverse':True}, 'lims-dewar-add-container'),
    (r'^shipping/shipment/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source': Shipment, 'object': Dewar, 'reverse': True}, 'lims-dewar-remove'),
    (r'^shipping/dewar/(?P<src_id>\d+)/container/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source':Dewar, 'object':Container, 'reverse':True}, 'lims-dewar-remove-container'),

    #########################
    (r'^shipping/container/basic/$', 'unassigned_object_list', {'model': Container, 'related_field': 'dewar', 'template': 'objlist/basic_object_list.html'}, 'lims-container-basic-list'),
    #CONTAINERS##############    
    (r'^shipping/container/$', 'object_list', {'model': Container, 'template': 'objlist/generic_list.html', 'can_add': True, 'link': True}, 'lims-container-list'),
    (r'^containers/crystal/basic/$', 'container_crystal_list', {'model': Crystal, 'template': 'objlist/basic_object_list.html', }, 'lims-crystal-container-list'),
    (r'^shipping/container/(?P<id>\d+)/$', 'object_detail', {'model': Container, 'template': 'lims/entries/container.html'}, 'lims-container-detail'),
    (r'^shipping/container/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-edit'),
    (r'^shipping/container/(?P<id>\d+)/remove/$', 'remove_object', {'model': Container, 'field':'dewar'}, 'lims-container-remove'),
    (r'^shipping/container/(?P<id>\d+)/new/$', 'add_new_object', {'model': Crystal, 'form': SampleForm, 'field': 'container'}, 'lims-container-new-crystal'),
    #(r'^shipping/container/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'form': SampleSelectForm, 'parent_model': Container, 'field': 'container', 'additional_fields': ['container_location']}, 'lims-container-add-crystal'),
    (r'^shipping/container/new/$', 'create_object', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-new'),
    (r'^shipping/container/(?P<dest_id>\d+)/widget/.*/crystal/(?P<obj_id>\d+)/loc/(?P<loc_id>\w{1,2})/$', 'add_existing_object', {'destination':Container, 'object':Crystal, 'reverse':True}, 'lims-container-add-crystal'),
    (r'^containers/crystal/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-container-edit-crystal'),
    (r'^shipping/container/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/remove/$', 'remove_object', {'source':Container, 'object':Crystal, 'reverse':True}, 'lims-container-remove-crystal'),

    #######################
    (r'^samples/crystal/basic/$', 'basic_crystal_list', {'model': Crystal, 'template': 'objlist/basic_object_list.html', }, 'lims-crystal-basic-list'),
    #CRYSTALS##############
    (r'^samples/crystal/$', 'object_list', {'model': Crystal, 'template': 'objlist/generic_list.html', 'can_add': True, 'link': True}, 'lims-crystal-list'),
    (r'^samples/crystal/(?P<id>\d+)/$', 'crystal_object_detail', {'model': Crystal, 'template': 'lims/entries/crystal.html'}, 'lims-crystal-detail'),
    (r'^samples/crystal/new/$',  'create_object', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-new'),
    (r'^samples/crystal/(?P<id>\d+)/priority/$', 'priority', {'model': Crystal, 'field': 'priority'}, 'lims-crystal-priority'),
    (r'^samples/crystal/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-edit'),
    # this url removes a crystal from a container. 
    (r'^samples/crystal/(?P<id>\d+)/remove/$', 'remove_object', {'model': Crystal, 'field':'container'}, 'lims-crystal-remove'),
    (r'^samples/crystal/(?P<id>\d+)/delete/$', 'delete_object', {'model': Crystal, 'form': ConfirmDeleteForm,'orphan_models' : []}, 'lims-crystal-delete'),
    (r'^samples/crystal/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object':Cocktail, 'replace': True}, 'lims-crystal-add-cocktail'),
    (r'^samples/crystal/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystalform/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object': CrystalForm, 'replace':True}, 'lims-crystal-add-crystalform'),

    ########################
    (r'^samples/cocktail/basic/$', 'basic_object_list', {'model': Cocktail, 'template': 'objlist/basic_object_list.html' }, 'lims-cocktail-basic-list'),
    #COCKTAILS##############
    (r'^samples/cocktail/$', 'object_list', {'model': Cocktail, 'template': 'objlist/generic_list.html', 'can_add': True, 'modal_edit': True, 'delete_inline': True}, 'lims-cocktail-list'),
    (r'^samples/cocktail/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-edit'),
    (r'^samples/cocktail/(?P<id>\d+)/delete/$', 'delete_object', {'model': Cocktail, 'form': ConfirmDeleteForm,'orphan_models' : [(Crystal, 'cocktail')]}, 'lims-cocktail-delete'),
    (r'^samples/cocktail/new/$', 'create_object', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-new'),

    ############################
    (r'^samples/crystalform/basic/$', 'basic_object_list', {'model': CrystalForm, 'template': 'objlist/basic_object_list.html'}, 'lims-crystalform-basic-list'),
    #(r'^samples/crystalform/(?P<id>\d+)/$', 'object_detail', {'model': CrystalForm, 'template': 'lims/entries/crystalform.html'}, 'lims-crystalform-detail'),
    #CRYSTAL FORMS##############
    (r'^samples/crystalform/$', 'object_list', {'model': CrystalForm, 'template': 'objlist/generic_list.html', 'can_add': True, 'modal_edit': True, 'delete_inline': True}, 'lims-crystalform-list'),
    (r'^samples/crystalform/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-edit'),
    (r'^samples/crystalform/(?P<id>\d+)/delete/$', 'delete_object', {'model': CrystalForm, 'form': ConfirmDeleteForm,'orphan_models' : [(Crystal, 'crystal_form')]}, 'lims-crystalform-delete'),
    (r'^samples/crystalform/new/$', 'create_object', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-new'),

    #######################
    #REQUESTS##############
    (r'^experiment/request/$', 'object_list', {'model': Experiment, 'template': 'objlist/generic_list.html', 'can_add': True, 'link': True}, 'lims-experiment-list'),
    (r'^experiment/request/(?P<id>\d+)/$', 'experiment_object_detail', {'model': Experiment, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/request/(?P<id>\d+)/edit/$','edit_object_inline', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),
    (r'^experiment/request/(?P<id>\d+)/delete/$', 'delete_object', {'model': Experiment, 'form': ConfirmDeleteForm, 'orphan_models': []}, 'lims-experiment-delete'),
    (r'^experiment/request/new/$', 'create_object', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-new'),
    (r'^experiment/request/(?P<id>\d+)/priority/$', 'priority', {'model': Experiment, 'field': 'priority'}, 'lims-experiment-priority'),
    (r'^experiment/request/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'parent_model': Experiment, 'field':'experiment'}, 'lims-experiment-add-crystal'),
    (r'^experiment/request/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-add-crystal'),
    (r'^experiment/experiment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'remove_object', {'source':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-remove-crystal'),

    ######################
    #REPORTS##############
    (r'^experiment/report/$', 'object_list', {'model': Result, 'template': 'objlist/generic_list.html', 'link': True}, 'lims-result-list'),
    (r'^experiment/report/(?P<id>\d+)/$', 'object_detail', {'model': Result, 'template': 'lims/entries/result.html'} , 'lims-result-detail'),

    ####################
    #SCANS##############
    (r'^experiment/scan/$', 'object_list', {'model': ScanResult, 'template': 'objlist/generic_list.html'}, 'lims-scan-list'),
    (r'^experiment/scan/(?P<id>\d+)/$', 'object_detail', {'model': Result, 'template': 'lims/entries/scan.html'} , 'lims-scan-detail'),

    #######################
    #DATASETS##############
    (r'^experiment/dataset/$', 'object_list', {'model': Data, 'template': 'objlist/generic_list.html', 'modal_link': True}, 'lims-dataset-list'),
    (r'^experiment/dataset/(?P<id>\d+)/$', 'data_viewer', {}, 'lims-dataset-detail'),
    ###############


    #(r'^experiment/dataset/$', 'object_list', {'model': Data, 'template': 'objlist/object_list.html'}, 'lims-dataset-list'),
    #(r'^experiment/dataset/(?P<id>\d+)/$', 'object_detail', {'model': Data, 'template': 'lims/entries/experiment.html'} , 'lims-dataset-detail'),

    
    (r'^experiment/crystal/(?P<id>\d+)/rescreen/$', 'rescreen', {}, 'lims-crystal-rescreen'),
    (r'^experiment/crystal/(?P<id>\d+)/recollect/$', 'recollect', {}, 'lims-crystal-recollect'),
    (r'^experiment/crystal/(?P<id>\d+)/complete/$', 'complete', {}, 'lims-crystal-complete'),

    (r'^experiment/result/resubmit/$','create_object', {'model': Experiment, 'form': ExperimentFromStrategyForm, 'template': 'objforms/form_base.html', 'action': 'resubmit', 'redirect': 'lims-experiment-list'}, 'lims-strategy-experiment-new'),        

    url(r'^experiment/result/(\d+)/shellstats.png$', 'plot_shell_stats', name='lims-plot-shells'),
    url(r'^experiment/result/(\d+)/framestats.png$', 'plot_frame_stats', name='lims-plot-frames'),
    url(r'^experiment/result/(\d+)/diffstats.png$', 'plot_diff_stats', name='lims-plot-diffs'),
    url(r'^experiment/result/(\d+)/stderr.png$', 'plot_error_stats', name='lims-plot-stderr'),
    url(r'^experiment/result/(\d+)/profiles.png$', 'plot_profiles_stats', name='lims-plot-profiles'),
    url(r'^experiment/result/(\d+)/wilson.png$', 'plot_wilson_stats', name='lims-plot-wilson'),
    url(r'^experiment/result/(\d+)/twinning.png$', 'plot_twinning_stats', name='lims-plot-twinning'),

    (r'^activity/$', 'object_list', {'model': ActivityLog, 'template': 'objlist/generic_list.html'}, 'lims-activity-log'),
    
    #new model handling urls (rest style, src/src_id/dest/dest_id/object/obj_id)
    # samples page
    (r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'remove_object', {'source':Crystal, 'object':Cocktail}, 'lims-crystal-remove-cocktail'),
    (r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystalform/(?P<obj_id>\d+)/$', 'remove_object', {'source':Crystal, 'object':CrystalForm}, 'lims-crystal-remove-crystalform'),

    # experiments page
    # due to these models working differently (experiment main page, but it's a property on crystal) handled abnormal

    
    # shipments page
    (r'^shipping/dewar/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'remove_object', {'source':Dewar, 'object':Container, 'reverse':True}, 'lims-shipment-remove-container'),
    (r'^shipping/shipment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'remove_object', {'source':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-remove-dewar'),

)


urlpatterns += patterns('django.views.generic.simple',
    (r'^shipping/$', 'redirect_to', {'url': '/lims/shipping/shipment/'}),
    (r'^experiment/$', 'redirect_to', {'url': '/lims/experiment/request/'}),
    (r'^samples/$', 'redirect_to', {'url': '/lims/samples/crystal/'}),
)

urlpatterns += patterns('',
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join('media/')}),
)

if settings.DEBUG:
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

