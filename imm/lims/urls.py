from django.conf.urls.defaults import *
import lims.models
import lims.forms

urlpatterns = patterns('lims.views',
    (r'^$', 'show_project'),
    (r'^shipping/$', 'shipping_summary'),
    (r'^shipping/shipment/$', 'project_object_list', {'model': lims.models.Shipment, 'template': 'lims/lists/shipping_list.html'}, 'lims-shipment-list'),
    (r'^shipping/shipment/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Shipment, 'template': 'lims/entries/shipment.html'}, 'lims-shipment-detail'),
    (r'^shipping/shipment/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.Shipment, 'form': lims.forms.ShipmentForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-edit'),
    (r'^shipping/shipment/(?P<id>\d+)/send/$', 'edit_object_inline', {'model': lims.models.Shipment, 'form': lims.forms.ShipmentSendForm, 'template': 'objforms/form_base.html'}, 'lims-shipment-send'),
    (r'^shipping/shipment/(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Dewar, 'form': lims.forms.DewarForm, 'field':'shipment'}, 'lims-shipment-new-dewar'),
    (r'^shipping/shipment/(?P<id>\d+)/add/$', 'add_existing_object', {'model': lims.models.Dewar, 'parent_model': lims.models.Shipment, 'field':'shipment'}, 'lims-shipment-add-dewar'), 
    (r'^shipping/shipment/new/$', 'create_object', {'model': lims.models.Shipment, 'form': lims.forms.ShipmentForm, 'template': 'lims/forms/shipping_base.html'}, 'lims-shipment-new'),
    #(r'^shipping/shipment/delete/(?P<id>\d+)/$', 'delete_shipment'),
    
    (r'^shipping/dewar/$', 'project_object_list', {'model': lims.models.Dewar, 'template': 'lims/lists/shipping_list.html'}, 'lims-dewar-list'),
    (r'^shipping/dewar/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Dewar, 'template': 'lims/entries/dewar.html'}, 'lims-dewar-detail'),
    (r'^shipping/dewar/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.Dewar, 'form': lims.forms.DewarForm, 'template': 'objforms/form_base.html'}, 'lims-dewar-edit'),
    (r'^shipping/dewar/(?P<id>\d+)/remove/$', 'remove_object', {'model': lims.models.Dewar, 'field':'shipment'}, 'lims-dewar-remove'),
    (r'^shipping/dewar/(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Container, 'form': lims.forms.ContainerForm, 'field':'dewar'}, 'lims-dewar-new-container'),
    (r'^shipping/dewar/(?P<id>\d+)/add/$', 'add_existing_object', {'model': lims.models.Container, 'parent_model': lims.models.Dewar, 'field':'dewar'}, 'lims-dewar-add-container'),
    (r'^shipping/dewar/new/$', 'create_object', {'model': lims.models.Dewar, 'form': lims.forms.DewarForm, 'template': 'lims/forms/shipping_base.html'}, 'lims-dewar-new'),
    #(r'^shipping/dewar/delete/(?P<id>\d+)/$', 'delete_dewar'),
    
    (r'^shipping/container/$', 'project_object_list', {'model': lims.models.Container, 'template': 'lims/lists/shipping_list.html'}, 'lims-container-list'),
    (r'^shipping/container/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Container, 'template': 'lims/entries/container.html'}, 'lims-container-detail'),
    (r'^shipping/container/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.Container, 'form': lims.forms.ContainerForm, 'template': 'objforms/form_base.html'}, 'lims-container-edit'),
    (r'^shipping/container/(?P<id>\d+)/remove/$', 'remove_object', {'model': lims.models.Container, 'field':'dewar'}, 'lims-container-remove'),
    (r'^shipping/container/(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Crystal, 'form': lims.forms.SampleForm, 'field': 'container'}, 'lims-container-new-crystal'),
    (r'^shipping/container/new/$', 'create_object', {'model': lims.models.Container, 'form': lims.forms.ContainerForm, 'template': 'lims/forms/shipping_base.html'}, 'lims-container-new'),
    #(r'^shipping/container/delete/c(?P<id>\d+)/$', 'delete_container'),
    

    (r'^samples/$', 'sample_summary'),
    (r'^samples/crystal/$', 'project_object_list', {'model': lims.models.Crystal, 'template': 'lims/lists/samples_list.html'}, 'lims-crystal-list'),
    (r'^samples/crystal/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Crystal, 'template': 'lims/entries/crystal.html'}, 'lims-crystal-detail'),
    (r'^samples/crystal/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.Crystal, 'form': lims.forms.SampleForm, 'template': 'objforms/form_base.html'}, 'lims-crystal-edit'),
    (r'^samples/crystal/(?P<id>\d+)/remove/$', 'remove_object', {'model': lims.models.Crystal, 'field':'container'}, 'lims-crystal-remove'),
    (r'^samples/crystal/new/$',  'create_object', {'model': lims.models.Crystal, 'form': lims.forms.SampleForm, 'template': 'lims/forms/samples_base.html'}, 'lims-crystal-new'),
    #(r'^samples/crystal/delete/(?P<id>\d+)/$', 'delete_crystal'),

    (r'^samples/cocktail/$', 'project_object_list', {'model': lims.models.Cocktail, 'template': 'lims/lists/samples_list.html'}, 'lims-cocktail-list'),
    (r'^samples/cocktail/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Cocktail, 'template': 'lims/entries/cocktail.html'},  'lims-cocktail-detail'),
    (r'^samples/cocktail/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.Cocktail, 'form': lims.forms.CocktailForm, 'template': 'objforms/form_base.html'}, 'lims-cocktail-edit'),
    (r'^samples/cocktail/(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Constituent, 'form': lims.forms.ConstituentForm, 'field': 'cocktail'}, 'lims-cocktail-new-constituent'),
    (r'^samples/cocktail/(?P<id>\d+)/add/$', 'add_existing_object', {'model': lims.models.Constituent, 'parent_model': lims.models.Cocktail, 'field':'cocktail'}, 'lims-cocktail-add-constituent'),
    (r'^samples/cocktail/new/$', 'create_object', {'model': lims.models.Cocktail, 'form': lims.forms.CocktailForm, 'template': 'lims/forms/samples_base.html'}, 'lims-cocktail-new'),

    (r'^samples/crystalform/$', 'project_object_list', {'model': lims.models.CrystalForm, 'template': 'lims/lists/samples_list.html'}, 'lims-crystalform-list'),
    (r'^samples/crystalform/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.CrystalForm, 'template': 'lims/entries/crystalform.html'}, 'lims-crystalform-detail'),
    (r'^samples/crystalform/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.CrystalForm, 'form': lims.forms.CrystalFormForm, 'template': 'objforms/form_base.html'}, 'lims-crystalform-edit'),
    (r'^samples/crystalform/new/$', 'create_object', {'model': lims.models.CrystalForm, 'form': lims.forms.CrystalFormForm, 'template': 'lims/forms/samples_base.html'}, 'lims-crystalform-new'),

    (r'^samples/constituent/$', 'project_object_list', {'model': lims.models.Constituent, 'template': 'lims/lists/samples_list.html'}, 'lims-constituent-list'),
    (r'^samples/constituent/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Constituent, 'template': 'lims/entries/constituent.html'}, 'lims-constituent-detail'),
    (r'^samples/constituent/(?P<id>\d+)/edit/$', 'edit_object_inline', {'model': lims.models.Constituent, 'form': lims.forms.ConstituentForm, 'template': 'objforms/form_base.html'}, 'lims-constituent-edit'),
    (r'^samples/constituent/new/$', 'create_object', {'model': lims.models.Constituent, 'form': lims.forms.ConstituentForm, 'template': 'lims/forms/samples_base.html'}, 'lims-constituent-new'),

    (r'^experiment/$', 'experiment_summary'),
    (r'^experiment/request/$', 'project_object_list', {'model': lims.models.Experiment, 'template': 'lims/lists/experiment_list.html'}, 'lims-experiment-list'),
    (r'^experiment/request/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Experiment, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/request/(?P<id>\d+)/edit/$','edit_object_inline', {'model': lims.models.Experiment, 'form': lims.forms.ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),
    (r'^experiment/request/new/$', 'create_object', {'model': lims.models.Experiment, 'form': lims.forms.ExperimentForm}, 'lims-experiment-new'),

    (r'^experiment/result/$', 'project_object_list', {'model': lims.models.Result, 'template': 'lims/lists/experiment_list.html','can_add':False}, 'lims-experiment-list'),
    (r'^experiment/result/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Result, 'template': 'lims/entries/experiment.html'} , 'lims-experiment-detail'),
    (r'^experiment/result/(?P<id>\d+)/edit/$','edit_object_inline', {'model': lims.models.Result, 'form': lims.forms.ExperimentForm, 'template': 'objforms/form_base.html'}, 'lims-experiment-edit'),

    (r'^activity/$', 'user_object_list', {'model': lims.models.ActivityLog, 'template': 'objlist/generic_list.html','link': False, 'can_add': False}),
)

