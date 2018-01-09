from django.contrib import admin
from models import UserList, UserCategory, Announcement
from lims.models import Group, Container, Sample

from django import forms

runlist_site = admin.AdminSite()


class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('description', 'attachment', 'url')

admin.site.register(Announcement, AnnouncementAdmin)


class UserListAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description', 'address']
    list_filer = ['created', 'modified', 'active']
    list_display = ['id', 'name', 'address', 'description', 'active', 'modified']
    ordering = ['-created']

admin.site.register(UserList, UserListAdmin)
admin.site.register(UserCategory)