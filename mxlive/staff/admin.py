from django.contrib import admin
from models import Runlist, Link, UserList, Adaptor
from lims.models import Group, Container, Sample

from django import forms

runlist_site = admin.AdminSite()


class RunlistAdminForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.filter(status__in=[Group.STATES.ACTIVE, Group.STATES.PROCESSING]).filter(
            pk__in=Sample.objects.filter(
                status__in=[Sample.STATES.SENT, Sample.STATES.ON_SITE, Sample.STATES.LOADED]).values('group')),
        required=False)

    class Meta:
        model = Runlist
        fields = []


class RunlistAdmin(admin.ModelAdmin):
    search_fields = ['name', 'beamline__name', 'containers__name']
    list_filter = ['status', 'created']
    list_display = ('name', 'beamline', 'created', 'status')
    list_per_page = 16
    ordering = ['-created']
    form = RunlistAdminForm


admin.site.register(Runlist, RunlistAdmin)


class AdaptorAdmin(admin.ModelAdmin):
    search_fields = ['name', 'containers__name']
    list_filter = ['modified', 'created']
    list_display = ('name', 'created', 'modified')
    list_per_page = 16
    ordering = ['-created']

admin.site.register(Adaptor, AdaptorAdmin)


class LinkAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'document', 'url', 'modified')
    list_filter = ['category', 'modified']


admin.site.register(Link, LinkAdmin)


class GroupRunlistAdmin(admin.ModelAdmin):
    search_fields = ['comments', 'name']
    list_filter = []
    list_display = ('project', 'id', 'name', 'kind', 'plan', 'num_samples', 'status')
    ordering = ['-priority', '-created']
    unsortable = list_display
    list_per_page = 999999


runlist_site.register(Group, GroupRunlistAdmin)


class ContainerRunlistAdmin(admin.ModelAdmin):
    ordering = ['-created']
    search_fields = ['name', 'code']
    list_filter = ['modified']
    list_display = ('project', 'id', 'name', 'groups', 'capacity', 'num_samples', 'status')
    list_per_page = 999999
    unsortable = list_display


runlist_site.register(Container, ContainerRunlistAdmin)




class UserListAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description', 'address']
    list_filer = ['created', 'modified', 'active']
    list_display = ['id', 'name', 'address', 'description', 'active', 'modified']
    ordering = ['-created']


admin.site.register(UserList, UserListAdmin)
