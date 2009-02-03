from django.contrib import admin
from models import *

class MessageAdmin(admin.ModelAdmin):
    search_fields = ['subject','body']
    list_filter = ['status','date_sent']
    list_display = ('subject','date_sent')
    ordering = ['-date_sent']
    list_per_page = 10

admin.site.register(Message, MessageAdmin)

