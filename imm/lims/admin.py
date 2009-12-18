from django.contrib import admin
from models import *

class ConstituentAdmin(admin.ModelAdmin):
    search_fields = ['acronym', 'name', 'hazard_details']
    list_filter = ['kind','source','modified']
    list_display = ('id','acronym', 'name', 'kind', 'source')
    list_per_page = 10
    list_editable = ['acronym', 'name', 'kind', 'source']
    actions = None
    ordering = ['acronym']
admin.site.register(Constituent, ConstituentAdmin)

class ShipmentAdmin(admin.ModelAdmin):
    search_fields = ['label', 'comments','status']
    list_filter = ['status','created']
    list_display = ('id','label', 'status', 'date_shipped', 'carrier', 'num_dewars')
    list_per_page = 10
    actions = None
    ordering = ['-created']
admin.site.register(Shipment, ShipmentAdmin)

class DewarAdmin(admin.ModelAdmin):
    search_fields = ['label', 'comments']
    list_filter = ['modified','created']
    list_display = ('id', 'label', 'code', 'created', 'modified', 'num_containers')
    ordering = ['-created']
    actions = None
    list_per_page = 10
admin.site.register(Dewar, DewarAdmin)
    
class ActivityLogAdmin(admin.ModelAdmin):
    list_filter = ['action_type','created']
    search_fields = ['description','ip_number']
    list_display = ('content_type','created','action_type','user','ip_number','description')
    ordering = ('-created',)
    list_per_page = 10
    actions = None
admin.site.register(ActivityLog, ActivityLogAdmin)
        
        
class ExperimentAdmin(admin.ModelAdmin):
    search_fields = ['comments','name']
    list_filter = ['plan','status','kind','modified']
    list_display = ('id','name','kind','status','plan','num_crystals')
    ordering = ['-created']
    list_per_page = 10
    actions = None
admin.site.register(Experiment, ExperimentAdmin)

class CrystalAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code']
    list_filter = ['modified']
    list_display = ('id', 'name', 'crystal_form', 'cocktail', 'container', 'container_location')       
    ordering = ['-created']
    actions = None
    list_per_page = 10
admin.site.register(Crystal, CrystalAdmin)

class CocktailAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['comments','constituents']
    list_filter = ['modified',]
    list_display = ('id', 'name', 'created','modified')
    actions = None
admin.site.register(Cocktail, CocktailAdmin)
    
class CrystalFormAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','space_group']
    list_filter = ['modified',]
    list_display = ('id', 'name', 'cell_a', 'cell_b', 'cell_c','cell_alpha', 'cell_beta', 'cell_gamma', 'space_group' )
    list_per_page = 10
    actions = None
admin.site.register(CrystalForm, CrystalFormAdmin)

class SpaceGroupAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','code']
    list_filter = ['crystal_system','lattice_type']
    list_display = ('id', 'name', 'crystal_system', 'lattice_type')
    actions = None
        
        
class ContainerAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['label','code']
    list_filter = ['modified','kind']
    list_display = ('id', 'label', 'code', 'capacity', 'created', 'modified', 'num_crystals')
    list_per_page = 10
    actions = None
admin.site.register(Container, ContainerAdmin)

admin.site.register(Project)
admin.site.register(Carrier)
admin.site.register(SpaceGroup)
admin.site.register(Laboratory)

