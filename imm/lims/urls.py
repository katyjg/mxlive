from django.conf.urls.defaults import patterns
from imm.lims.models import *
from imm.lims.forms import *

urlpatterns = patterns('imm.lims.views',
    (r'^$', 'show_project'),
    (r'^shipping/$', 'shipping_summary'),
    (r'^shipping/shipment/$', 'project_object_list', {'model': Shipment, 'template': 'lims/lists/shipping_list.html'}, 'lims-shipment-list'),
    (r'^shipping/shipment/(?P<id>\d+)/$', 'object_detail', {'model': Shipment, 'template': 'lims/entries/shipment.html'}, 'lims-shipment-detail'),
    (r'^shipping/shipment/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-edit'),
    (r'^shipping/shipment/(?P<id>\d+)/send/$', 'edit_object_inline', {'model': Shipment, 'form': ShipmentSendForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-send'),
    (r'^shipping/shipment/(?P<id>\d+)/new/$', 'add_new_object', {'model': Dewar, 'form': DewarForm, 'field':'shipment'}, 'lims-shipment-new-dewar'),
    (r'^shipping/shipment/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Dewar, 'parent_model': Shipment, 'field':'shipment'}, 'lims-shipment-add-dewar'), 
    (r'^shipping/shipment/new/$', 'create_object', {'model': Shipment, 'form': ShipmentForm, 'template': 'lims/forms/shipping_base.html'}, 'lims-shipment-new'),
    #(r'^shipping/shipment/delete/(?P<id>\d+)/$', 'delete_shipment'),
    
    (r'^shipping/dewar/$', 'project_object_list', {'model': Dewar, 'template': 'lims/lists/shipping_list.html'}, 'lims-dewar-list'),
    (r'^shipping/dewar/(?P<id>\d+)/$', 'object_detail', {'model': Dewar, 'template': 'lims/entries/dewar.html'}, 'lims-dewar-detail'),
    (r'^shipping/dewar/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Dewar, 'form': DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-edit'),
    (r'^shipping/dewar/(?P<id>\d+)/remove/$', 'remove_object', {'model': Dewar, 'field':'shipment'}, 'lims-dewar-remove'),
    (r'^shipping/dewar/(?P<id>\d+)/new/$', 'add_new_object', {'model': Container, 'form': ContainerForm, 'field':'dewar'}, 'lims-dewar-new-container'),
    (r'^shipping/dewar/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Container, 'parent_model': Dewar, 'field':'dewar'}, 'lims-dewar-add-container'),
    (r'^shipping/dewar/new/$', 'create_object', {'model': Dewar, 'form': DewarForm, 'template': 'lims/forms/shipping_base.html'}, 'lims-dewar-new'),
    #(r'^shipping/dewar/delete/(?P<id>\d+)/$', 'delete_dewar'),
    
    (r'^shipping/container/$', 'project_object_list', {'model': Container, 'template': 'lims/lists/shipping_list.html'}, 'lims-container-list'),
    (r'^shipping/container/(?P<id>\d+)/$', 'object_detail', {'model': Container, 'template': 'lims/entries/container.html'}, 'lims-container-detail'),
    (r'^shipping/container/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Container, 'form': ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-edit'),
    (r'^shipping/container/(?P<id>\d+)/remove/$', 'remove_object', {'model': Container, 'field':'dewar'}, 'lims-container-remove'),
    (r'^shipping/container/(?P<id>\d+)/new/$', 'add_new_object', {'model': Crystal, 'form': SampleForm, 'field': 'container'}, 'lims-container-new-crystal'),
    (r'^shipping/container/new/$', 'create_object', {'model': Container, 'form': ContainerForm, 'template': 'lims/forms/shipping_base.html'}, 'lims-container-new'),
    #(r'^shipping/container/delete/c(?P<id>\d+)/$', 'delete_container'),
    

    (r'^samples/$', 'sample_summary'),
    (r'^samples/crystal/$', 'project_object_list', {'model': Crystal, 'template': 'lims/lists/samples_list.html'}, 'lims-crystal-list'),
    (r'^samples/crystal/(?P<id>\d+)/$', 'object_detail', {'model': Crystal, 'template': 'lims/entries/crystal.html'}, 'lims-crystal-detail'),
    (r'^samples/crystal/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Crystal, 'form': SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-edit'),
    (r'^samples/crystal/(?P<id>\d+)/remove/$', 'remove_object', {'model': Crystal, 'field':'container'}, 'lims-crystal-remove'),
    (r'^samples/crystal/new/$',  'create_object', {'model': Crystal, 'form': SampleForm, 'template': 'lims/forms/samples_base.html'}, 'lims-crystal-new'),
    #(r'^samples/crystal/delete/(?P<id>\d+)/$', 'delete_crystal'),

    (r'^samples/cocktail/$', 'project_object_list', {'model': Cocktail, 'template': 'lims/lists/samples_list.html'}, 'lims-cocktail-list'),
    (r'^samples/cocktail/(?P<id>\d+)/$', 'object_detail', {'model': Cocktail, 'template': 'lims/entries/cocktail.html'},  'lims-cocktail-detail'),
    (r'^samples/cocktail/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Cocktail, 'form': CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-edit'),
    (r'^samples/cocktail/(?P<id>\d+)/new/$', 'add_new_object', {'model': Constituent, 'form': ConstituentForm, 'field': 'cocktail'}, 'lims-cocktail-new-constituent'),
    (r'^samples/cocktail/(?P<id>\d+)/add/$', 'add_existing_object', {'model': Constituent, 'parent_model': Cocktail, 'field':'cocktail'}, 'lims-cocktail-add-constituent'),
    (r'^samples/cocktail/new/$', 'create_object', {'model': Cocktail, 'form': CocktailForm, 'template': 'lims/forms/samples_base.html'}, 'lims-cocktail-new'),

    (r'^samples/crystalform/$', 'project_object_list', {'model': CrystalForm, 'template': 'lims/lists/samples_list.html'}, 'lims-crystalform-list'),
    (r'^samples/crystalform/(?P<id>\d+)/$', 'object_detail', {'model': CrystalForm, 'template': 'lims/entries/crystalform.html'}, 'lims-crystalform-detail'),
    (r'^samples/crystalform/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-edit'),
    (r'^samples/crystalform/new/$', 'create_object', {'model': CrystalForm, 'form': CrystalFormForm, 'template': 'lims/forms/samples_base.html'}, 'lims-crystalform-new'),

    (r'^samples/constituent/$', 'project_object_list', {'model': Constituent, 'template': 'lims/lists/samples_list.html'}, 'lims-constituent-list'),
    (r'^samples/constituent/(?P<id>\d+)/$', 'object_detail', {'model': Constituent, 'template': 'lims/entries/constituent.html'}, 'lims-constituent-detail'),
    (r'^samples/constituent/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': Constituent, 'form': ConstituentForm, 'template': 'objforms/form_base.html'}, 'lims-constituent-edit'),
    (r'^samples/constituent/new/$', 'create_object', {'model': Constituent, 'form': ConstituentForm, 'template': 'lims/forms/samples_base.html'}, 'lims-constituent-new'),

    (r'^experiment/$', 'experiment_summary'),
    (r'^experiment/request/$', 'project_object_list', {'model': Experiment, 'template': 'lims/lists/experiment_list.html'}, 'lims-experiment-list'),
    (r'^experiment/request/(?P<id>\d+)/$', 'object_detail', {'model': Experiment, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/request/(?P<id>\d+)/edit/$','edit_object_inline', {'model': Experiment, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),
    (r'^experiment/request/new/$', 'create_object', {'model': Experiment, 'form': ExperimentForm}, 'lims-experiment-new'),

    (r'^experiment/result/$', 'project_object_list', {'model': Result, 'template': 'lims/lists/experiment_list.html','can_add':False}, 'lims-experiment-list'),
    (r'^experiment/result/(?P<id>\d+)/$', 'object_detail', {'model': Result, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/result/(?P<id>\d+)/edit/$','edit_object_inline', {'model': Result, 'form': ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),

    (r'^activity/$', 'user_object_list', {'model': ActivityLog, 'template': 'objlist/generic_list.html','link': False, 'can_add': False}),
)


