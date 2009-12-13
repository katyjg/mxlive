from django.conf.urls.defaults import *
import lims.models
import lims.forms

urlpatterns = patterns('lims.views',
    (r'^$', 'show_project'),
    (r'^shipping/$', 'shipping_summary'),
    (r'^shipping/shipment/$', 'project_object_list', {'model': lims.models.Shipment, 'template': 'lims/lists/shipping_list.html'}),
    (r'^shipping/shipment/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Shipment, 'template': 'lims/entries/shipment.html'} ),
    (r'^shipping/shipment/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Shipment, 'form': lims.forms.ShipmentForm, 'template': 'objforms/form_base.html'}),
    (r'^shipping/shipment/f(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Shipment, 'form': lims.forms.ShipmentSendForm, 'template': 'objforms/form_base.html'}),
    (r'^shipping/shipment/c(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Dewar, 'form': lims.forms.DewarForm, 'field':'shipment'}),
    #(r'^shipping/shipment/c(?P<id>\d+)/add/$', 'shipment_add_dewar'),   
    (r'^shipping/shipment/new/$', 'create_object', {'model': lims.models.Shipment, 'form': lims.forms.ShipmentForm, 'template': 'lims/forms/shipping_base.html'}),
    #(r'^shipping/shipment/complete/(?P<id>\d+)/$', 'complete_shipment'),
    #(r'^shipping/shipment/delete/(?P<id>\d+)/$', 'delete_shipment'),
    
    (r'^shipping/dewar/$', 'project_object_list', {'model': lims.models.Dewar, 'template': 'lims/lists/shipping_list.html'}),
    (r'^shipping/dewar/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Dewar, 'template': 'lims/entries/dewar.html'} ),
    (r'^shipping/dewar/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Dewar, 'form': lims.forms.DewarForm, 'template': 'objforms/form_base.html'}),
    (r'^shipping/dewar/u(?P<id>\d+)/$', 'remove_object', {'model': lims.models.Dewar, 'field':'shipment'}),
    (r'^shipping/dewar/c(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Container, 'form': lims.forms.ContainerForm, 'field':'dewar'}),
    #(r'^shipping/dewar/c(?P<id>\d+)/add/$', 'dewar_add_container'),
    (r'^shipping/dewar/new/$', 'create_object', {'model': lims.models.Dewar, 'form': lims.forms.DewarForm, 'template': 'lims/forms/shipping_base.html'}),
    #(r'^shipping/dewar/delete/(?P<id>\d+)/$', 'delete_dewar'),
    #(r'^shipping/dewar/recycle/(?P<id>\d+)/$', 'recycle_dewar'),
    
    (r'^shipping/container/$', 'project_object_list', {'model': lims.models.Container, 'template': 'lims/lists/shipping_list.html'}),
    (r'^shipping/container/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Container, 'template': 'lims/entries/container.html'} ),
    (r'^shipping/container/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Container, 'form': lims.forms.ContainerForm, 'template': 'objforms/form_base.html'}),
    (r'^shipping/container/u(?P<id>\d+)/$', 'remove_object', {'model': lims.models.Container, 'field':'dewar'}),
    (r'^shipping/container/c(?P<id>\d+)/new/$', 'add_new_object', {'model': lims.models.Crystal, 'form': lims.forms.SampleForm, 'field': 'container'}),
    #(r'^shipping/container/c(?P<id>\d+)/add/$', 'container_add_sample'),    
    (r'^shipping/container/new/$', 'create_object', {'model': lims.models.Container, 'form': lims.forms.ContainerForm, 'template': 'lims/forms/shipping_base.html'}),
    #(r'^shipping/container/delete/c(?P<id>\d+)/$', 'delete_container'),
    #(r'^shipping/container/recycle/(?P<id>\d+)/$', 'recycle_container'),
    

    (r'^samples/$', 'sample_summary'),
    (r'^samples/crystal/$', 'project_object_list', {'model': lims.models.Crystal, 'template': 'lims/lists/samples_list.html'}),
    (r'^samples/crystal/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Crystal, 'template': 'lims/entries/crystal.html'} ),
    (r'^samples/crystal/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Crystal, 'form': lims.forms.SampleForm, 'template': 'objforms/form_base.html'}),
    (r'^samples/crystal/new/$',  'create_object', {'model': lims.models.Crystal, 'form': lims.forms.SampleForm, 'template': 'lims/forms/samples_base.html'}),
    #(r'^samples/crystal/delete/(?P<id>\d+)/$', 'delete_crystal'),
    #(r'^samples/crystal/recycle/(?P<id>\d+)/$', 'recycle_crystal'),

    (r'^samples/cocktail/$', 'project_object_list', {'model': lims.models.Cocktail, 'template': 'lims/lists/samples_list.html'}),
    (r'^samples/cocktail/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Cocktail, 'template': 'lims/entries/cocktail.html'} ),
    (r'^samples/cocktail/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Cocktail, 'form': lims.forms.CocktailForm, 'template': 'objforms/form_base.html'}),
    #(r'^samples/cocktail/c(?P<id>\d+)/new/$', 'cocktail_new_constituent'),
    #(r'^samples/cocktail/c(?P<id>\d+)/add/$', 'cocktail_add_constituent'),
    (r'^samples/cocktail/new/$', 'create_object', {'model': lims.models.Cocktail, 'form': lims.forms.CocktailForm, 'template': 'lims/forms/samples_base.html'}),

    (r'^samples/crystalform/$', 'project_object_list', {'model': lims.models.CrystalForm, 'template': 'lims/lists/samples_list.html'}),
    (r'^samples/crystalform/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.CrystalForm, 'template': 'lims/entries/crystalform.html'}),
    (r'^samples/crystalform/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.CrystalForm, 'form': lims.forms.CrystalFormForm, 'template': 'objforms/form_base.html'}),
    (r'^samples/crystalform/new/$', 'create_object', {'model': lims.models.CrystalForm, 'form': lims.forms.CrystalFormForm, 'template': 'lims/forms/samples_base.html'}),

    (r'^samples/constituent/$', 'project_object_list', {'model': lims.models.Constituent, 'template': 'lims/lists/samples_list.html'}),
    (r'^samples/constituent/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Constituent, 'template': 'lims/entries/constituent.html'}),
    (r'^samples/constituent/e(?P<id>\d+)/$', 'edit_object_inline', {'model': lims.models.Constituent, 'form': lims.forms.ConstituentForm, 'template': 'objforms/form_base.html'}),
    (r'^samples/constituent/new/$', 'create_object', {'model': lims.models.Constituent, 'form': lims.forms.ConstituentForm, 'template': 'lims/forms/samples_base.html'}),

    (r'^experiment/$', 'experiment_summary'),
    (r'^experiment/request/$', 'project_object_list', {'model': lims.models.Experiment, 'template': 'lims/lists/experiment_list.html'}),
    (r'^experiment/request/(?P<id>\d+)/$', 'object_detail', {'model': lims.models.Experiment, 'template': 'lims/entries/experiment.html'} ),
    (r'^experiment/request/new/$', 'create_object', {'model': lims.models.Experiment, 'form': lims.forms.ExperimentForm}),
    (r'^experiment/request/e(?P<id>\d+)/$','edit_object_inline', {'model': lims.models.Experiment, 'form': lims.forms.ExperimentForm, 'template': 'objforms/form_base.html'}),

    (r'^activity/$', 'user_object_list', {'model': lims.models.ActivityLog, 'template': 'lims/lists/generic_list.html','link': False, 'can_add': False}),
)

