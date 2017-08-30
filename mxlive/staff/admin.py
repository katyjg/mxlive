from django.contrib import admin
from models import Link, UserList
from lims.models import Group, Container, Sample

from django import forms

runlist_site = admin.AdminSite()


class LinkAdmin(admin.ModelAdmin):
    list_display = ('category', 'description', 'document', 'url', 'modified')
    list_filter = ['category', 'modified']


admin.site.register(Link, LinkAdmin)


class UserListAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description', 'address']
    list_filer = ['created', 'modified', 'active']
    list_display = ['id', 'name', 'address', 'description', 'active', 'modified']
    ordering = ['-created']


admin.site.register(UserList, UserListAdmin)
