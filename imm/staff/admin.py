from django.contrib import admin
from imm.staff.models import Runlist
from imm.lims.models import Experiment
from imm.lims.models import Container

runlist_site = admin.AdminSite()

class RunlistAdmin(admin.ModelAdmin):
    list_filter = ['status','created']
    list_display = ('id','name', 'status', 'container_list', 'num_containers')
    list_per_page = 10
    ordering = ['-priority', '-created']
admin.site.register(Runlist, RunlistAdmin)

class ExperimentRunlistAdmin(admin.ModelAdmin):
    search_fields = ['comments','name']
    list_filter = []
    list_display = ('id','project','name','kind','status','plan','num_crystals')
    filter_horizontal = ['crystals']
    ordering = ['-staff_priority', '-priority', '-created']
    unsortable = list_display
    list_per_page = 999999
runlist_site.register(Experiment, ExperimentRunlistAdmin)

class ContainerRunlistAdmin(admin.ModelAdmin):
    ordering = ['-staff_priority', '-created']
    search_fields = ['label','code']
    list_filter = ['modified','kind']
    list_display = ('experiments', 'id', 'label', 'code', 'capacity', 'num_crystals')
    list_per_page = 999999
    unsortable = list_display
runlist_site.register(Container, ContainerRunlistAdmin)
