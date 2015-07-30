from django.contrib import admin
from reversion.admin import VersionAdmin
from .models import *  # @UnusedWildImport
from objlist.filters import WeeklyDateFilter

ITEMS_PER_PAGE = 16
ACTIVITY_ITEMS_PER_PAGE = 6
staff_site = admin.AdminSite()

class ShipmentAdmin(VersionAdmin):
    search_fields = ['project__name','name', 'comments','status']
    list_filter = ['created','status']
    list_display = ('identity','name', 'date_shipped', '_Carrier', 'num_dewars', 'status')
    list_per_page = ITEMS_PER_PAGE    
    ordering = ['-created']
admin.site.register(Shipment, ShipmentAdmin)

class ShipmentStaffAdmin(ShipmentAdmin):
    list_display = ('project','identity','name', 'date_shipped', '_Carrier', 'num_dewars', 'status')
staff_site.register(Shipment, ShipmentStaffAdmin)

class DewarAdmin(VersionAdmin):
    search_fields = ['project__name','name', 'comments','shipment__name','status']
    list_filter = ['modified','status']
    list_display = ('identity', 'name', '_Shipment', 'modified', 'num_containers', 'status')
    ordering = ['-created']    
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Dewar, DewarAdmin)

class DewarStaffAdmin(DewarAdmin):
    list_display = ('project', 'identity', 'name', '_Shipment', 'modified', 'num_containers', 'status')
staff_site.register(Dewar, DewarStaffAdmin)

class ContainerAdmin(VersionAdmin):
    ordering = ['-created']
    search_fields = ['project__name','name', 'comments']
    list_filter = ['modified','kind']
    list_display = ('identity', 'name', '_Dewar', 'kind', 'capacity', 'num_crystals', 'status')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Container, ContainerAdmin)

class ContainerStaffAdmin(ContainerAdmin):
    list_display = ('project', 'identity', 'name', '_Dewar', 'kind', 'capacity', 'num_crystals', 'status')
    ordering = ['-staff_priority', '-created']
staff_site.register(Container, ContainerStaffAdmin)
    
class ExperimentAdmin(VersionAdmin):
    search_fields = ['project__name','comments','name']
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
    search_fields = ['project__name','name', 'barcode', 'comments', 'crystal_form__name', 'cocktail__name']
    list_filter = ['modified','status']
    list_display = ('identity', 'name', '_Cocktail', '_Crystal_form', 'comments', '_Container', 'container_location', 'status')       
    ordering = ['-created', '-priority']
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Crystal, CrystalAdmin)

class CrystalStaffAdmin(CrystalAdmin):
    list_display = ('project', 'identity', 'name', '_Cocktail', '_Crystal_form', 'comments', '_Container', 'container_location', 'status')     
    ordering = ['-staff_priority', '-priority', '-created']
staff_site.register(Crystal, CrystalStaffAdmin)

class ResultAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['project__name','name','crystal__name','space_group__name']
    list_filter = ['modified','kind']
    list_display = ('id', 'name', 'frames', 'space_group', 'resolution', 'r_meas', 'completeness', 'score', 'kind')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Result, ResultAdmin)

class ResultStaffAdmin(ResultAdmin):
    list_filter = ['modified','kind','status']
    list_display = ('project','id','name','resolution','kind','frames','created','status')
    ordering = ['-created', 'project']
staff_site.register(Result, ResultStaffAdmin)

class ScanResultAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['project__name','name','crystal__name', 'beamline__name']
    list_filter = ['modified','kind']
    list_display = ('id', 'name', 'crystal', 'edge', 'kind', 'created')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(ScanResult, ScanResultAdmin)

class ScanResultStaffAdmin(ScanResultAdmin):
    list_filter = ['modified','kind','status','beamline']
    list_display = ('project','id','name','edge','kind','created','beamline')
    ordering = ['-created', 'project']
staff_site.register(ScanResult, ScanResultStaffAdmin)

class DataAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['id','name','beamline__name','delta_angle','crystal__name','frame_sets','project__name']
    list_filter = ['modified', 'kind']
    list_display = ('id', 'name', '_Crystal','frame_sets', 'delta_angle', 'total_angle', 'wavelength', 'beamline', 'kind')
    list_per_page = ITEMS_PER_PAGE
admin.site.register(Data, DataAdmin)

class DataStaffAdmin(DataAdmin):
    list_filter = ['modified','kind','status','beamline']
    list_display = ('project','id','name','_Crystal','beamline','kind','created','status','download')
    ordering = ['-created', 'project']
staff_site.register(Data, DataStaffAdmin)

class CocktailAdmin(VersionAdmin):
    ordering = ['-created']
    search_fields = ['project__name','description','name',]
    list_filter = ['modified']
    list_display = ('identity', 'name', 'description', 'modified')    
admin.site.register(Cocktail, CocktailAdmin)

class CrystalFormAdmin(VersionAdmin):
    ordering = ['-created']
    search_fields = ['project__name','name','space_group__name']
    list_filter = ['modified']
    list_display = ('identity', 'name', 'cell_a', 'cell_b', 'cell_c','cell_alpha', 'cell_beta', 'cell_gamma', '_Space_group' )
    list_per_page = ITEMS_PER_PAGE    
admin.site.register(CrystalForm, CrystalFormAdmin)

class SpaceGroupAdmin(admin.ModelAdmin):
    ordering = ['id']
    search_fields = ['name','code']
    list_filter = ['crystal_system','lattice_type']
    list_display = ('id', 'name', 'crystal_system', 'lattice_type')
admin.site.register(SpaceGroup, SpaceGroupAdmin)
           
class ProjectAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name','city','province','contact_person','department','organisation','country']
    list_filter = ['modified','carrier']
    list_display = ('name','contact_person','city','province','department','organisation','contact_phone')
admin.site.register(Project, ProjectAdmin)           
           
class ActivityLogAdmin(admin.ModelAdmin):
    list_filter = [WeeklyDateFilter]
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

admin.site.register(Carrier)
admin.site.register(Session)
admin.site.register(Beamline)

# admin.py
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class ProfileInline(admin.StackedInline):
    model = Project
    fk_name = 'user'
    max_num = 1

class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline,]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)