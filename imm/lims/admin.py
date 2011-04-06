from django.contrib import admin
from reversion.admin import VersionAdmin
from imm.lims.models import *

ITEMS_PER_PAGE = 16
ACTIVITY_ITEMS_PER_PAGE = 6
staff_site = admin.AdminSite()

class ShipmentAdmin(VersionAdmin):
    search_fields = ['name', 'comments','status']
    list_filter = ['created','status']
    list_display = ('identity','name', 'date_shipped', 'carrier', 'num_dewars', 'status')
    list_per_page = ITEMS_PER_PAGE    
    ordering = ['-created']
admin.site.register(Shipment, ShipmentAdmin)

class ShipmentStaffAdmin(ShipmentAdmin):
    list_display = ('project','identity','name', 'date_shipped', 'carrier', 'num_dewars', 'status')
staff_site.register(Shipment, ShipmentStaffAdmin)

class DewarAdmin(VersionAdmin):
    search_fields = ['name', 'comments']
    list_filter = ['modified']
    list_display = ('identity', 'name', 'shipment', 'modified', 'num_containers', 'status')
    ordering = ['-created']    
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Dewar, DewarAdmin)

class DewarStaffAdmin(DewarAdmin):
    list_display = ('project', 'identity', 'name', 'shipment', 'modified', 'num_containers', 'status')
staff_site.register(Dewar, DewarStaffAdmin)

class ContainerAdmin(VersionAdmin):
    ordering = ['-created']
    search_fields = ['name', 'comments']
    list_filter = ['modified','kind']
    list_display = ('identity', 'name', 'kind', 'capacity', 'num_crystals', 'status')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Container, ContainerAdmin)

class ContainerStaffAdmin(ContainerAdmin):
    list_display = ('project', 'identity', 'name', 'kind', 'capacity', 'num_crystals', 'status')
    ordering = ['-staff_priority', '-created']
staff_site.register(Container, ContainerStaffAdmin)
    
class ExperimentAdmin(VersionAdmin):
    search_fields = ['comments','name']
    list_filter = ['modified','status']
    list_display = ('identity','name','kind','plan','num_crystals','status')
    ordering = ('-modified', '-priority')
    list_per_page = ITEMS_PER_PAGE   
admin.site.register(Experiment, ExperimentAdmin)

class ExperimentStaffAdmin(ExperimentAdmin):
    list_display = ('project','identity','name','kind','plan','num_crystals','status')
    ordering = ['-staff_priority', '-priority', '-created']
staff_site.register(Experiment, ExperimentStaffAdmin)

class CrystalAdmin(VersionAdmin):
    search_fields = ['name', 'barcode', 'comments']
    list_filter = ['modified','status']
    list_display = ('identity', 'name', 'cocktail', 'comments', 'container', 'container_location', 'status')       
    ordering = ['-created', '-priority']
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Crystal, CrystalAdmin)

class CrystalStaffAdmin(CrystalAdmin):
    list_display = ('identity', 'name', 'cocktail', 'comments', 'container', 'container_location', 'status')     
    ordering = ['-staff_priority', '-priority', '-created']
staff_site.register(Crystal, CrystalStaffAdmin)

class CocktailAdmin(VersionAdmin):
    ordering = ['-created']
    search_fields = ['description','name',]
    list_filter = ['modified']
    list_display = ('identity', 'name', 'description', 'modified')    
admin.site.register(Cocktail, CocktailAdmin)
    
class CrystalFormAdmin(VersionAdmin):
    ordering = ['-created']
    search_fields = ['name','space_group__name']
    list_filter = ['modified']
    list_display = ('identity', 'name', 'cell_a', 'cell_b', 'cell_c','cell_alpha', 'cell_beta', 'cell_gamma', 'space_group' )
    list_per_page = ITEMS_PER_PAGE    
admin.site.register(CrystalForm, CrystalFormAdmin)

class SpaceGroupAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','code']
    list_filter = ['crystal_system','lattice_type']
    list_display = ('id', 'name', 'crystal_system', 'lattice_type')
admin.site.register(SpaceGroup, SpaceGroupAdmin)
           
class ResultAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name','crystal__name','space_group__name']
    list_filter = ['modified','kind']
    list_display = ('id', 'name', 'data', 'space_group', 'resolution', 'r_meas', 'completeness', 'score', 'kind')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Result, ResultAdmin)

class DataAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name','beamline__name']
    list_filter = ['modified', 'kind']
    list_display = ('id', 'name', 'crystal','frame_sets', 'delta_angle', 'total_angle', 'wavelength', 'kind')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Data, DataAdmin)

class StrategyAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name']
    list_filter = ['modified']
    list_display = ('identity', 'name', 'result', 'start_angle', 'delta_angle', 'total_angle', 'exposure_time', 'energy', 'exp_completeness')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Strategy, StrategyAdmin)

class ActivityLogAdmin(admin.ModelAdmin):
    list_filter = ['created']
    search_fields = ['description','ip_number', 'content_type__name', 'action_type']
    list_display = ('created', 'action_type','user_description','ip_number','object_repr','description')
    ordering = ('-created',)
    list_per_page = ACTIVITY_ITEMS_PER_PAGE    
admin.site.register(ActivityLog, ActivityLogAdmin)

class FeedbackAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['project','message', 'contact_name']
    list_filter = ['created', 'category']
    list_display = ('project', 'contact_name', 'contact', 'category', 'message')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Feedback, FeedbackAdmin)

admin.site.register(Project)
admin.site.register(Carrier)
admin.site.register(Session)
admin.site.register(Beamline)

