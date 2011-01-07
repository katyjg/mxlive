from django.conf.urls.defaults import patterns, url
from django.contrib import databrowse
from imm.lims.models import *
from imm.lims.forms import *

urlpatterns = patterns('imm.lims.views',
    (r'^$', 'show_project', {}, 'project-home'),
    (r'^browse/(.*)', databrowse.site.root),
    (r'^shipping/$', 'shipping_summary', {'model': ActivityLog}, 'lims-shipping-summary'),

    #SHIPMENTS##############
    (r'^shipping/shipments/$', 'object_list', {'model': Shipment, 'template': 'objlist/generic_list.html', 'can_add': True, 'can_upload': False, 'is_individual': True }, 'lims-shipment-list'),
    (r'^shipping/shipments/(?P<id>\d+)/$', 'object_detail', {'model': Shipment, 'template': 'lims/entries/shipment.html'}, 'lims-shipment-detail'),
    (r'^shipping/shipments/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-edit'),
    (r'^shipping/shipments/(?P<id>\d+)/send/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentSendForm, 'template': 'objforms/form_base.html', 'action' : 'send'}, 'lims-shipment-send'),
    (r'^shipping/shipments/(?P<id>\d+)/new/$', 'add_new_object', {'model': Dewar, 'form': DewarForm, 'field':'shipment'}, 'lims-shipment-new-dewar'),
    (r'^shipping/shipments/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Dewar, 'parent_model': Shipment, 'field':'shipment'}, 'lims-shipment-add-dewar'), 
    (r'^shipping/shipments/(?P<id>\d+)/delete/$', 'delete_object', {'model': Shipment, 'form': ShipmentDeleteForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-delete'),
    (r'^shipping/shipments/(?P<id>\d+)/close/$', 'close_object', {'model' : Shipment, 'form': ShipmentDeleteForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-close'),
    (r'^shipping/shipments/(?P<id>\d+)/pdf/$', 'shipment_pdf', {}, 'lims-shipment-pdf'),
    (r'^shipping/shipments/(?P<id>\d+)/xls/$', 'shipment_xls', {}, 'lims-shipment-pdf'),
    (r'^shipping/shipments/new/$', 'create_object', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-new'),
    (r'^shipping/shipments/upload/$', 'upload_shipment', {'model': Shipment, 'form': ShipmentUploadForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-upload'),
    (r'^shipping/shipments/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-add-dewar'),
    (r'^shipping/shipments/(?P<id>\d+)/widget/(?P<src_id>\d+)/dewar/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Shipment, 'object':Container}, 'lims-shipment-add-container'),
    #####################
    #DEWARS##############
    (r'^shipping/dewars/$', 'object_list', {'model': Dewar, 'template': 'objlist/generic_list.html', 'can_add': True, 'is_individual': True}, 'lims-dewar-list'),
    (r'^shipping/dewars/(?P<id>\d+)/$', 'object_detail', {'model': Dewar, 'template': 'lims/entries/dewar.html'}, 'lims-dewar-detail'),
    (r'^shipping/dewars/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-edit'),
    (r'^shipping/dewars/(?P<id>\d+)/remove/$', 'remove_object', {'model': Dewar, 'field':'shipment'}, 'lims-dewar-remove'),
    (r'^shipping/dewars/(?P<id>\d+)/new/$', 'add_new_object', {'model': Container, 'form': ContainerForm, 'field':'dewar'}, 'lims-dewar-new-container'),
    (r'^shipping/dewars/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Container, 'parent_model': Dewar, 'field':'dewar'}, 'lims-dewar-add-container'),
    (r'^shipping/dewars/new/$', 'create_object', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-new'),
    (r'^shipping/dewars/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/none/0/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Dewar, 'object':Container, 'reverse':True}, 'lims-dewar-add-container'),
    #########################
    #CONTAINERS##############    
    (r'^shipping/containers/$', 'object_list', {'model': Container, 'template': 'objlist/generic_list.html', 'can_add': True, 'can_receive': True, 'is_individual': True}, 'lims-container-list'),
    (r'^shipping/containers/(?P<id>\d+)/$', 'object_detail', {'model': Container, 'template': 'lims/entries/container.html'}, 'lims-container-detail'),
    (r'^shipping/containers/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-edit'),
    (r'^shipping/containers/(?P<id>\d+)/remove/$', 'remove_object', {'model': Container, 'field':'dewar'}, 'lims-container-remove'),
    (r'^shipping/containers/(?P<id>\d+)/new/$', 'add_new_object', {'model': Crystal, 'form': SampleForm, 'field': 'container'}, 'lims-container-new-crystal'),
    (r'^shipping/containers/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'form': SampleSelectForm, 'parent_model': Container, 'field': 'container', 'additional_fields': ['container_location']}, 'lims-container-add-crystal'),
    (r'^shipping/containers/new/$', 'create_object', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-new'),
    (r'^shipping/containers/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Container, 'object':Crystal, 'reverse':True}, 'lims-container-add-crystal'),
    #######################
    #CRYSTALS##############
    (r'^samples/crystals/$', 'object_list', {'model': Crystal, 'template': 'objlist/generic_list.html', 'can_add': True, 'can_prioritize': True, 'is_individual': True}, 'lims-crystal-list'),
    (r'^samples/crystals/(?P<id>\d+)/$', 'crystal_object_detail', {'model': Crystal, 'template': 'lims/entries/crystal.html'}, 'lims-crystal-detail'),
    (r'^samples/crystals/new/$',  'create_object', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-new'),
    (r'^samples/crystals/(?P<id>\d+)/up/$', 'change_priority', {'model': Crystal, 'action': 'up', 'field': 'priority'}, 'lims-crystal-up'),
    (r'^samples/crystals/(?P<id>\d+)/down/$', 'change_priority', {'model': Crystal, 'action': 'down', 'field': 'priority'}, 'lims-crystal-up'),
    (r'^samples/crystals/(?P<id>\d+)/priority/$', 'priority', {'model': Crystal, 'field': 'priority'}, 'lims-crystal-priority'),
    (r'^samples/crystals/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-edit'),
    # this url removes a crystal from a container. 
    (r'^samples/crystals/(?P<id>\d+)/remove/$', 'remove_object', {'model': Crystal, 'field':'container'}, 'lims-crystal-remove'),
    (r'^samples/crystals/(?P<id>\d+)/delete/$', 'delete_object', {'model': Crystal, 'form': ShipmentDeleteForm,'orphan_models' : []}, 'lims-crystal-delete'),
    (r'^samples/crystals/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object':Cocktail, 'replace': True}, 'lims-crystal-add-cocktail'),
    (r'^samples/crystals/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystal_form/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object': CrystalForm, 'replace':True}, 'lims-crystal-add-crystalform'),
    ########################
    #COCKTAILS##############
    (r'^samples/cocktails/$', 'object_list', {'model': Cocktail, 'template': 'objlist/generic_list.html', 'can_add': True}, 'lims-cocktail-list'),
    (r'^samples/cocktails/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-edit'),
    (r'^samples/cocktails/new/$', 'create_object', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-new'),
    ############################
    #CRYSTAL FORMS##############
    (r'^samples/crystalforms/$', 'object_list', {'model': CrystalForm, 'template': 'objlist/generic_list.html', 'can_add': True}, 'lims-crystalform-list'),
    (r'^samples/crystalforms/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-edit'),
    (r'^samples/crystalforms/new/$', 'create_object', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-new'),
    #######################
    #REQUESTS##############
    (r'^experiment/requests/$', 'object_list', {'model': Experiment, 'template': 'objlist/generic_list.html', 'can_add': True, 'can_prioritize': True, 'is_individual': True}, 'lims-experiment-list'),
    (r'^experiment/requests/(?P<id>\d+)/$', 'experiment_object_detail', {'model': Experiment, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/requests/(?P<id>\d+)/edit/$','edit_object_inline', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),
    (r'^experiment/requests/(?P<id>\d+)/delete/$', 'delete_object', {'model': Experiment, 'form': ShipmentDeleteForm, 'orphan_models': []}, 'lims-experiment-delete'),
    (r'^experiment/requests/new/$', 'create_object', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-new'),
    (r'^experiment/requests/(?P<id>\d+)/up/$', 'change_priority', {'model': Experiment, 'action': 'up', 'field': 'priority'}, 'lims-experiment-up'),
    (r'^experiment/requests/(?P<id>\d+)/down/$', 'change_priority', {'model': Experiment, 'action': 'down', 'field': 'priority'}, 'lims-experiment-up'),
    (r'^experiment/requests/(?P<id>\d+)/priority/$', 'priority', {'model': Experiment, 'field': 'priority'}, 'lims-experiment-priority'),
    (r'^experiment/requests/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'parent_model': Experiment, 'field':'experiment'}, 'lims-experiment-add-crystal'),
    (r'^experiment/requests/(?P<dest_id>\d+)/widget/(?P<src_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-add-crystal'),
    ######################
    #REPORTS##############
    (r'^experiment/reports/$', 'object_list', {'model': Result, 'template': 'objlist/generic_list.html'}, 'lims-result-list'),
    (r'^experiment/reports/(?P<id>\d+)/$', 'object_detail', {'model': Result, 'template': 'lims/entries/result.html'} , 'lims-result-detail'),
    (r'^experiment/reports/(?P<id>\d+)/print/$', 'result_print', {}, 'lims-result-print'),
    ####################
    #SCANS##############
    (r'^experiment/scans/$', 'object_list', {'model': ScanResult, 'template': 'objlist/generic_list.html'}, 'lims-scan-list'),
    (r'^experiment/scans/(?P<id>\d+)/$', 'object_detail', {'model': Result, 'template': 'lims/entries/scan.html'} , 'lims-scan-detail'),
    #######################
    #DATASETS##############
    (r'^experiment/datasets/$', 'object_list', {'model': Data, 'template': 'objlist/generic_list.html'}, 'lims-dataset-list'),
    ###############

    #(r'^shipping/shipment/$', 'object_list', {'model': Shipment, 'template': 'objlist/object_list.html', 'can_add': True, 'can_upload': True }, 'lims-shipment-list'),
    (r'^shipping/shipment/(?P<id>\d+)/$', 'object_detail', {'model': Shipment, 'template': 'lims/entries/shipment.html'}, 'lims-shipment-detail'),
    (r'^shipping/shipment/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-edit'),
    (r'^shipping/shipment/(?P<id>\d+)/send/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentSendForm, 'template': 'objforms/form_base.html', 'action' : 'send'}, 'lims-shipment-send'),
    (r'^shipping/shipment/(?P<id>\d+)/new/$', 'add_new_object', {'model': Dewar, 'form': DewarForm, 'field':'shipment'}, 'lims-shipment-new-dewar'),
    (r'^shipping/shipment/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Dewar, 'parent_model': Shipment, 'field':'shipment'}, 'lims-shipment-add-dewar'), 
    (r'^shipping/shipment/(?P<id>\d+)/delete/$', 'delete_object', {'model': Shipment, 'form': ShipmentDeleteForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-delete'),
    #(r'^shipping/shipment/(?P<id>\d+)/delete/$', 'delete_object', {'model': Shipment , 'form': ShipmentDeleteForm, 'redirect': 'lims-shipping-summary', 'template':'objforms/form_base.html'}, 'lims-shipment-delete'), #orphan_models' : [(Dewar, 'shipment')]}, 'lims-shipment-delete'),
    #(r'^shipping/shipment/(?P<id>\d+)/delete/$', 'delete_object', {'model': Shipment, 'redirect' : 'lims-shipping-summary', 'orphan_models' : [(Dewar, 'shipment')]}, 'lims-shipment-delete'),
    (r'^shipping/shipment/(?P<id>\d+)/close/$', 'close_object', {'model' : Shipment, 'form': ShipmentDeleteForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-close'),
    (r'^shipping/shipment/(?P<id>\d+)/pdf/$', 'shipment_pdf', {}, 'lims-shipment-pdf'),
    (r'^shipping/shipment/(?P<id>\d+)/xls/$', 'shipment_xls', {}, 'lims-shipment-pdf'),
    (r'^shipping/shipment/new/$', 'create_object', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-new'),
    (r'^shipping/shipment/upload/$', 'upload_shipment', {'model': Shipment, 'form': ShipmentUploadForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-upload'),
    #(r'^shipping/shipment/delete/(?P<id>\d+)/$', 'delete_shipment'),

    #(r'^shipping/dewar/$', 'object_list', {'model': Dewar, 'template': 'objlist/object_list.html', 'can_add': True}, 'lims-dewar-list'),
    (r'^shipping/dewar/basic/$', 'basic_object_list', {'model': Dewar, 'template': 'objlist/basic_object_list.html'}, 'lims-dewar-basic-list'),
    (r'^shipping/dewar/(?P<id>\d+)/$', 'object_detail', {'model': Dewar, 'template': 'lims/entries/dewar.html'}, 'lims-dewar-detail'),
    (r'^shipping/dewar/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-edit'),
    (r'^shipping/dewar/(?P<id>\d+)/remove/$', 'remove_object', {'model': Dewar, 'field':'shipment'}, 'lims-dewar-remove'),
    (r'^shipping/dewar/(?P<id>\d+)/new/$', 'add_new_object', {'model': Container, 'form': ContainerForm, 'field':'dewar'}, 'lims-dewar-new-container'),
    (r'^shipping/dewar/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Container, 'parent_model': Dewar, 'field':'dewar'}, 'lims-dewar-add-container'),
    (r'^shipping/dewar/new/$', 'create_object', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-new'),
    #(r'^shipping/dewar/delete/(?P<id>\d+)/$', 'delete_dewar'),

    #(r'^shipping/container/$', 'object_list', {'model': Container, 'template': 'objlist/object_list.html', 'can_add': True}, 'lims-container-list'),
    (r'^shipping/container/basic/$', 'basic_object_list', {'model': Container, 'template': 'objlist/basic_object_list.html'}, 'lims-container-basic-list'),
    (r'^shipping/container/(?P<id>\d+)/$', 'object_detail', {'model': Container, 'template': 'lims/entries/container.html'}, 'lims-container-detail'),
    (r'^shipping/container/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-edit'),
    (r'^shipping/container/(?P<id>\d+)/remove/$', 'remove_object', {'model': Container, 'field':'dewar'}, 'lims-container-remove'),
    (r'^shipping/container/(?P<id>\d+)/new/$', 'add_new_object', {'model': Crystal, 'form': SampleForm, 'field': 'container'}, 'lims-container-new-crystal'),
    (r'^shipping/container/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'form': SampleSelectForm, 'parent_model': Container, 'field': 'container', 'additional_fields': ['container_location']}, 'lims-container-add-crystal'),
    (r'^shipping/container/new/$', 'create_object', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-new'),
    #(r'^shipping/container/delete/c(?P<id>\d+)/$', 'delete_container'),

    (r'^containers/$', 'container_summary', {'model': ActivityLog}, 'lims-container-summary'),
    (r'^containers/crystal/basic/$', 'container_crystal_list', {'model': Crystal, 'template': 'objlist/basic_object_list.html', }, 'lims-crystal-container-list'),
    (r'^containers/crystal/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-edit'),
    (r'^containers/request/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'parent_model': Container, 'field':'container'}, 'lims-container-add-crystal'),
    (r'^containers/widget/(?P<src_id>\d+)/container/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Container, 'object':Crystal, 'reverse':True}, 'lims-container-add-crystal'),
    (r'^containers/container/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'remove_object', {'source':Container, 'object':Crystal, 'reverse':True}, 'lims-experiment-remove-crystal'),

    (r'^samples/$', 'sample_summary', {'model': ActivityLog}, 'lims-sample-summary'),
    #(r'^samples/crystal/$', 'object_list', {'model': Crystal, 'template': 'objlist/object_list.html', 'can_add': True, 'can_prioritize': True}, 'lims-crystal-list'),
    (r'^samples/crystal/basic/$', 'basic_crystal_list', {'model': Crystal, 'template': 'objlist/basic_object_list.html', }, 'lims-crystal-basic-list'),
    (r'^samples/crystal/(?P<id>\d+)/$', 'object_detail', {'model': Crystal, 'template': 'lims/entries/crystal.html'}, 'lims-crystal-detail'),
    (r'^samples/crystal/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-edit'),
    # this url removes a crystal from a container. 
    (r'^samples/crystal/(?P<id>\d+)/remove/$', 'remove_object', {'model': Crystal, 'field':'container'}, 'lims-crystal-remove'),
    
    (r'^samples/crystal/(?P<id>\d+)/delete/$', 'delete_object', {'model': Crystal, 'form': ShipmentDeleteForm,'orphan_models' : []}, 'lims-crystal-delete'),
    (r'^samples/crystal/new/$',  'create_object', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-new'),
    #(r'^samples/crystal/delete/(?P<id>\d+)/$', 'delete_crystal'),
    (r'^samples/crystal/(?P<id>\d+)/up/$', 'change_priority', {'model': Crystal, 'action': 'up', 'field': 'priority'}, 'lims-crystal-up'),
    (r'^samples/crystal/(?P<id>\d+)/down/$', 'change_priority', {'model': Crystal, 'action': 'down', 'field': 'priority'}, 'lims-crystal-up'),
    (r'^samples/crystal/(?P<id>\d+)/priority/$', 'priority', {'model': Crystal, 'field': 'priority'}, 'lims-crystal-priority'),

    #(r'^samples/cocktail/$', 'object_list', {'model': Cocktail, 'template': 'objlist/object_list.html', 'can_add': True}, 'lims-cocktail-list'),
    (r'^samples/cocktail/basic/$', 'basic_object_list', {'model': Cocktail, 'template': 'objlist/basic_object_list.html' }, 'lims-cocktail-basic-list'),
    (r'^samples/cocktail/(?P<id>\d+)/$', 'object_detail', {'model': Cocktail, 'template': 'lims/entries/cocktail.html'},  'lims-cocktail-detail'),
    (r'^samples/cocktail/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-edit'),
    (r'^samples/cocktail/(?P<id>\d+)/new/$', 'add_new_object', {'model': Constituent, 'form': ConstituentForm, 'field': 'cocktail'}, 'lims-cocktail-new-constituent'),
    (r'^samples/cocktail/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Constituent, 'parent_model': Cocktail, 'field':'cocktail'}, 'lims-cocktail-add-constituent'),
    (r'^samples/cocktail/new/$', 'create_object', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-new'),

    #(r'^samples/crystalform/$', 'object_list', {'model': CrystalForm, 'template': 'objlist/object_list.html', 'can_add': True}, 'lims-crystalform-list'),
    (r'^samples/crystalform/basic/$', 'basic_object_list', {'model': CrystalForm, 'template': 'objlist/basic_object_list.html'}, 'lims-crystalform-basic-list'),
    (r'^samples/crystalform/(?P<id>\d+)/$', 'object_detail', {'model': CrystalForm, 'template': 'lims/entries/crystalform.html'}, 'lims-crystalform-detail'),
    (r'^samples/crystalform/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-edit'),
    (r'^samples/crystalform/new/$', 'create_object', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-new'),

    (r'^samples/constituent/$', 'object_list', {'model': Constituent, 'template': 'objlist/object_list.html', 'can_add': True}, 'lims-constituent-list'),
    (r'^samples/constituent/basic/$', 'basic_object_list', {'model': Constituent, 'template': 'objlist/basic_object_list.html'}, 'lims-constituent-basic-list'),
    (r'^samples/constituent/(?P<id>\d+)/$', 'object_detail', {'model': Constituent, 'template': 'lims/entries/constituent.html'}, 'lims-constituent-detail'),
    (r'^samples/constituent/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Constituent, 'form': ConstituentForm, 'template': 'objforms/form_base.html'}, 'lims-constituent-edit'),
    (r'^samples/constituent/new/$', 'create_object', {'model': Constituent, 'form': ConstituentForm, 'template': 'objforms/form_base.html'}, 'lims-constituent-new'),

    (r'^experiment/$', 'experiment_summary', {'model': ActivityLog}, 'lims-experiment-summary'),
    #(r'^experiment/request/$', 'object_list', {'model': Experiment, 'template': 'objlist/object_list.html', 'can_add': True, 'can_prioritize': True}, 'lims-experiment-list'),
    (r'^experiment/request/(?P<id>\d+)/$', 'experiment_object_detail', {'model': Experiment, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/request/(?P<id>\d+)/edit/$','edit_object_inline', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),
    (r'^experiment/request/(?P<id>\d+)/delete/$', 'delete_object', {'model': Experiment, 'form': ShipmentDeleteForm, 'orphan_models': []}, 'lims-experiment-delete'),
    (r'^experiment/request/new/$', 'create_object', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-new'),
    (r'^experiment/request/(?P<id>\d+)/up/$', 'change_priority', {'model': Experiment, 'action': 'up', 'field': 'priority'}, 'lims-experiment-up'),
    (r'^experiment/request/(?P<id>\d+)/down/$', 'change_priority', {'model': Experiment, 'action': 'down', 'field': 'priority'}, 'lims-experiment-up'),
    (r'^experiment/request/(?P<id>\d+)/priority/$', 'priority', {'model': Experiment, 'field': 'priority'}, 'lims-experiment-priority'),
    (r'^experiment/request/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Crystal, 'parent_model': Experiment, 'field':'experiment'}, 'lims-experiment-add-crystal'),

    (r'^experiment/result/$', 'object_list', {'model': Result, 'template': 'objlist/object_list.html'}, 'lims-result-list'),
    (r'^experiment/result/(?P<id>\d+)/$', 'object_detail', {'model': Result, 'template': 'lims/entries/result.html'} , 'lims-result-detail'),
    (r'^experiment/result/(?P<id>\d+)/print/$', 'result_print', {}, 'lims-result-print'),

    (r'^experiment/dataset/$', 'object_list', {'model': Data, 'template': 'objlist/object_list.html'}, 'lims-dataset-list'),
    #(r'^experiment/dataset/(?P<id>\d+)/$', 'object_detail', {'model': Data, 'template': 'lims/entries/experiment.html'} , 'lims-dataset-detail'),
    (r'^experiment/dataset/(?P<id>\d+)/$', 'data_viewer', {}, 'lims-dataset-detail'),
    
    (r'^experiment/crystal/(?P<id>\d+)/rescreen/$', 'rescreen', {}, 'lims-crystal-rescreen'),
    (r'^experiment/crystal/(?P<id>\d+)/recollect/$', 'recollect', {}, 'lims-crystal-recollect'),
    (r'^experiment/crystal/(?P<id>\d+)/complete/$', 'complete', {}, 'lims-crystal-complete'),

    (r'^experiment/strategy/$', 'object_list', {'model': Strategy, 'template': 'objlist/object_list.html'}, 'lims-strategy-list'),
    (r'^experiment/strategy/(?P<id>\d+)/$', 'object_detail', {'model': Strategy, 'template': 'lims/entries/experiment.html'} , 'lims-strategy-detail'),
    (r'^experiment/strategy/(?P<id>\d+)/reject/$','edit_object_inline', {'model': Strategy, 'form': StrategyRejectForm, 'template': 'objforms/form_base.html', 'action': 'reject'}, 'lims-strategy-edit'),
    #(r'^experiment/dataset/(?P<id>\d+)/edit/$','edit_object_inline', {'model': Data, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-strategy-edit'),

    (r'^experiment/result/resubmit/$','create_object', {'model': Experiment, 'form': ExperimentFromStrategyForm, 'template': 'objforms/form_base.html', 'action': 'resubmit', 'redirect': 'lims-experiment-list'}, 'lims-strategy-experiment-new'),        

    url(r'^experiment/result/(\d+)/shellstats.png$', 'plot_shell_stats', name='lims-plot-shells'),
    url(r'^experiment/result/(\d+)/framestats.png$', 'plot_frame_stats', name='lims-plot-frames'),
    url(r'^experiment/result/(\d+)/diffstats.png$', 'plot_diff_stats', name='lims-plot-diffs'),

    (r'^activity/$', 'object_list', {'model': ActivityLog, 'template': 'objlist/tiny_list.html','link': False}),
    
    #new model handling urls (rest style, src/src_id/dest/dest_id/object/obj_id)
    # samples page
    (r'^samples/widget/(?P<src_id>\d+)/crystal/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object':Cocktail, 'replace': True}, 'lims-crystal-add-cocktail'),
    (r'^samples/widget/(?P<src_id>\d+)/crystal/(?P<dest_id>\d+)/crystal_form/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Crystal, 'object': CrystalForm, 'replace':True}, 'lims-crystal-add-crystalform'),
    (r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/cocktail/(?P<obj_id>\d+)/$', 'remove_object', {'source':Crystal, 'object':Cocktail}, 'lims-crystal-remove-cocktail'),
    (r'^samples/crystal/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystal_form/(?P<obj_id>\d+)/$', 'remove_object', {'source':Crystal, 'object':CrystalForm}, 'lims-crystal-remove-crystalform'),

    # experiments page
    # due to these models working differently (experiment main page, but it's a property on crystal) handled abnormal
    (r'^experiment/widget/(?P<src_id>\d+)/experiment/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-add-crystal'),
    (r'^experiment/experiment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/crystal/(?P<obj_id>\d+)/$', 'remove_object', {'source':Experiment, 'object':Crystal, 'reverse':True}, 'lims-experiment-remove-crystal'),
    
    # shipments page
    (r'^shipping/widget/(?P<src_id>\d+)/shipment/(?P<dest_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-add-dewar'),
    (r'^shipping/widget/(?P<src_id>\d+)/dewar/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Dewar, 'object':Container, 'reverse':True}, 'lims-dewar-add-container'),
    (r'^shipping/widget/(?P<src_id>\d+)/shipment/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'add_existing_object', {'destination':Shipment, 'object':Container}, 'lims-shipment-add-container'),
    (r'^shipping/dewar/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/container/(?P<obj_id>\d+)/$', 'remove_object', {'source':Dewar, 'object':Container, 'reverse':True}, 'lims-shipment-remove-container'),
    (r'^shipping/shipment/(?P<src_id>\d+)/widget/(?P<dest_id>\d+)/dewar/(?P<obj_id>\d+)/$', 'remove_object', {'source':Shipment, 'object':Dewar, 'reverse':True}, 'lims-shipment-remove-dewar'),

)

from django.contrib import databrowse
_databrowse_model_list = [
            Project, 
            Laboratory, 
            Constituent, 
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
            ]
            
for mod in _databrowse_model_list:
    databrowse.site.register(mod)

