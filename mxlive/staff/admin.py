from django.contrib import admin
from models import Runlist, Link
from mxlive.lims.models import Experiment, Container, Crystal

from django import forms

runlist_site = admin.AdminSite()

class RunlistAdminForm(forms.ModelForm):
    experiments = forms.ModelMultipleChoiceField(
        queryset=Experiment.objects.filter(status__in=[Experiment.STATES.ACTIVE,Experiment.STATES.PROCESSING]).filter(pk__in=Crystal.objects.filter(status__in=[Crystal.STATES.SENT, Crystal.STATES.ON_SITE, Crystal.STATES.LOADED]).values('experiment')),
        required=False)

    class Meta:
        model = Runlist

class RunlistAdmin(admin.ModelAdmin):
    search_fields = ['name', 'beamline__name', 'containers__name']
    list_filter = ['status','created']
    list_display = ('name', 'beamline', 'created', 'status')
    list_per_page = 16
    ordering = ['-created']
    form = RunlistAdminForm
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
