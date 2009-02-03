from django.contrib import admin
from models import *

class ConstituentAdmin(admin.ModelAdmin):
    search_fields = ['acronym', 'name', 'hazard_details']
    list_filter = ['kind','source','modified']
    list_display = ('id','acronym', 'name', 'kind', 'source')
    list_per_page = 10
    ordering = ['acronym']

class ShipmentAdmin(admin.ModelAdmin):
    search_fields = ['label', 'comments','status']
    list_filter = ['status','created']
    list_display = ('id','label', 'status', 'date_shipped', 'carrier', 'num_dewars')
    list_per_page = 10
    ordering = ['-created']

class DewarAdmin(admin.ModelAdmin):
    search_fields = ['label', 'comments']
    list_filter = ['modified','created']
    list_display = ('id', 'label', 'code', 'created', 'modified', 'num_containers')
    ordering = ['-created']
    list_per_page = 10
    
class ActivityLogAdmin(admin.ModelAdmin):
    list_filter = ['action_type','created']
    search_fields = ['description','ip_number']
    list_display = ('content_type','created','action_type','user','ip_number','description')
    ordering = ('-created',)
    list_per_page = 10
        
        
class ExperimentAdmin(admin.ModelAdmin):
    search_fields = ['comments','name']
    list_filter = ['plan','status','kind','modified']
    list_display = ('id','name','kind','status','plan','num_crystals')
    ordering = ['-created']
    list_per_page = 10

class CrystalAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code']
    list_filter = ['modified']
    list_display = ('id', 'name', 'crystal_form', 'cocktail', 'container', 'container_location')       
    ordering = ['-created']
    list_per_page = 10

class CocktailAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['comments','constituents']
    list_filter = ['modified',]
    list_display = ('id', 'name', 'created','modified')
    
class CrystalFormAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','space_group']
    list_filter = ['modified',]
    list_display = ('id', 'name', 'cell_a', 'cell_b', 'cell_c','cell_alpha', 'cell_beta', 'cell_gamma', 'space_group' )
    list_per_page = 10

class SpaceGroupAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','code']
    list_filter = ['crystal_system','lattice_type']
    list_display = ('id', 'name', 'crystal_system', 'lattice_type')
        
        
class ContainerAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['label','code']
    list_filter = ['modified','kind']
    list_display = ('id', 'label', 'code', 'capacity', 'created', 'modified', 'num_crystals')
    list_per_page = 10

#class ResultAdmin(admin.ModelAdmin):

admin.site.register(Carrier)
admin.site.register(SpaceGroup)
admin.site.register(Project)
admin.site.register(Laboratory)
admin.site.register(Shipment, ShipmentAdmin)
admin.site.register(Dewar, DewarAdmin)
admin.site.register(Container, ContainerAdmin)
admin.site.register(Crystal, CrystalAdmin)
admin.site.register(CrystalForm, CrystalFormAdmin)
admin.site.register(Constituent, ConstituentAdmin)
admin.site.register(Cocktail, CocktailAdmin)
admin.site.register(ActivityLog, ActivityLogAdmin)
admin.site.register(Experiment, ExperimentAdmin)
