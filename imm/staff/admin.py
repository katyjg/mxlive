from django.contrib import admin
from imm.staff.models import Runlist, Link
from imm.lims.models import Experiment
from imm.lims.models import Container

runlist_site = admin.AdminSite()

class RunlistAdmin(admin.ModelAdmin):
    search_fields = ['name', 'beamline__name', 'containers__name']
    list_filter = ['status','created']
    list_display = ('name', 'beamline', 'created', 'status')
    list_per_page = 16
    ordering = ['-created']
admin.site.register(Runlist, RunlistAdmin)

class LinkAdmin(admin.ModelAdmin):
    list_display = ('category','description','document','url', 'modified')
    list_filter = ['category','modified']
admin.site.register(Link, LinkAdmin)

class ExperimentRunlistAdmin(admin.ModelAdmin):
    search_fields = ['comments','name']
    list_filter = []
    list_display = ('project','id','name','kind','plan','num_crystals','status')
    ordering = ['-staff_priority', '-priority', '-created']
    unsortable = list_display
    list_per_page = 999999
runlist_site.register(Experiment, ExperimentRunlistAdmin)

class ContainerRunlistAdmin(admin.ModelAdmin):
    ordering = ['-staff_priority', '-created']
    search_fields = ['name','code']
    list_filter = ['modified','kind']
    list_display = ('project', 'id', 'name', 'experiments', 'capacity', 'num_crystals', 'status')
    list_per_page = 999999
    unsortable = list_display
runlist_site.register(Container, ContainerRunlistAdmin)
