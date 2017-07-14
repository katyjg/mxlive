from django.contrib import admin
from reversion.admin import VersionAdmin
from models import *
from objlisto.filters import WeeklyDateFilter

ITEMS_PER_PAGE = 16
ACTIVITY_ITEMS_PER_PAGE = 6
staff_site = admin.AdminSite()

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



