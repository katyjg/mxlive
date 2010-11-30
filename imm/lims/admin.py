from django.contrib import admin
from imm.lims.models import *

staff_site = admin.AdminSite()

class ConstituentAdmin(admin.ModelAdmin):
    search_fields = ['acronym', 'name', 'hazard_details']
    list_filter = ['kind','source','modified']
    list_display = ('identity','acronym', 'name', 'kind', 'source')
    list_per_page = 10
    list_editable = ['acronym', 'name', 'kind', 'source']    
    ordering = ['acronym']
admin.site.register(Constituent, ConstituentAdmin)

class ShipmentAdmin(admin.ModelAdmin):
    search_fields = ['label', 'comments','status']
    list_filter = ['status','created']
    list_display = ('identity','label', 'status', 'date_shipped', 'carrier', 'num_dewars')
    list_per_page = 10    
    ordering = ['-created']
admin.site.register(Shipment, ShipmentAdmin)

class DewarAdmin(admin.ModelAdmin):
    search_fields = ['label', 'comments']
    list_filter = ['modified','created']
    list_display = ('identity', 'label', 'code', 'created', 'modified', 'num_containers')
    ordering = ['-created']    
    list_per_page = 10
admin.site.register(Dewar, DewarAdmin)
    
class ActivityLogAdmin(admin.ModelAdmin):
    list_filter = ['action_type','created']
    search_fields = ['description','ip_number']
    list_display = ('content_type','created','action_type','user','ip_number','description')
    ordering = ('-created',)
    list_per_page = 10    
admin.site.register(ActivityLog, ActivityLogAdmin)
        
class ExperimentAdmin(admin.ModelAdmin):
    search_fields = ['comments','name']
    list_filter = ['plan','status','kind','modified']
    list_display = ('identity','name','kind','status','plan','num_crystals')
#    list_display = ('id','name','kind','status','plan')
#    filter_horizontal = ['crystals']
    ordering = ('-priority', '-created')
    list_per_page = 10   
admin.site.register(Experiment, ExperimentAdmin)

class ExperimentStaffAdmin(ExperimentAdmin):
    list_display = ('identity','project','name','kind','status','plan','num_crystals')
    ordering = ['-staff_priority', '-priority', '-created']
staff_site.register(Experiment, ExperimentStaffAdmin)

class CrystalAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code']
    list_filter = ['modified']
#    list_display = ('id', 'name', 'crystal_form', 'cocktail', 'container', 'container_location')
    list_display = ('identity', 'name', 'status', 'cocktail', 'comments')       
    ordering = ['-priority', '-created']
    list_per_page = 10
admin.site.register(Crystal, CrystalAdmin)

class CrystalStaffAdmin(CrystalAdmin):
    ordering = ['-staff_priority', '-priority', '-created']
staff_site.register(Crystal, CrystalAdmin)

class CocktailAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['comments','constituents']
    list_filter = ['modified',]
    filter_horizontal = ['constituents']
    list_display = ('identity', 'name', 'created','modified')    
admin.site.register(Cocktail, CocktailAdmin)
    
class CrystalFormAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','space_group']
    list_filter = ['modified',]
    list_display = ('identity', 'name', 'cell_a', 'cell_b', 'cell_c','cell_alpha', 'cell_beta', 'cell_gamma', 'space_group' )
    list_per_page = 10    
admin.site.register(CrystalForm, CrystalFormAdmin)

class SpaceGroupAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','code']
    list_filter = ['crystal_system','lattice_type']
    list_display = ('id', 'name', 'crystal_system', 'lattice_type')
admin.site.register(SpaceGroup, SpaceGroupAdmin)
           
class ContainerAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['label','code']
    list_filter = ['modified','kind']
    list_display = ('identity', 'label', 'code', 'capacity', 'created', 'modified', 'num_crystals')
    list_per_page = 15
admin.site.register(Container, ContainerAdmin)

class ContainerStaffAdmin(ContainerAdmin):
    ordering = ['-staff_priority', '-created']
staff_site.register(Container, ContainerStaffAdmin)

class ResultAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name','crystal','score']
    list_filter = ['modified','kind']
    list_display = ('identity', 'name', 'crystal', 'score', 'space_group', 'resolution', 'r_meas', 'completeness')
    list_per_page = 15
admin.site.register(Result, ResultAdmin)

class DataAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name','url']
    list_filter = ['modified','detector', 'kind']
    list_display = ('id', 'name', 'crystal', 'frame_sets', 'delta_angle', 'total_angle', 'wavelength')
    list_per_page = 15
admin.site.register(Data, DataAdmin)

class StrategyAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name']
    list_filter = ['modified','status']
    list_display = ('identity', 'name', 'status', 'result', 'start_angle', 'delta_angle', 'total_angle', 'exposure_time', 'energy', 'exp_completeness')
    list_per_page = 15
admin.site.register(Strategy, StrategyAdmin)

admin.site.register(Project)
admin.site.register(Carrier)
admin.site.register(Laboratory)
admin.site.register(Session)
admin.site.register(Beamline)

