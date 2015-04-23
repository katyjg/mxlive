from django.contrib import admin
from models import *

class APIKeyAdmin(admin.ModelAdmin):
    search_fields = ['client_name', 'client_email', 'key', 'allowed_hosts']
    list_filer = ['created', 'modified', 'active']
    list_display = ['id', 'key', 'client_name', 'allowed_hosts', 'active', 'modified']
    ordering = ['-created']
admin.site.register(APIKey, APIKeyAdmin)

class APIKeyUsageAdmin(admin.ModelAdmin):
    search_fields = ['api_key__client_name', 'api_key__client_email', 'api_key__key', 'method', 'host']
    list_filer = ['created']
    list_display = ['id', 'api_key', 'host', 'method', 'created']
    ordering = ['-created']
admin.site.register(APIKeyUsage, APIKeyUsageAdmin)
