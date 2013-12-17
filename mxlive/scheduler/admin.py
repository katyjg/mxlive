from django.contrib import admin

from forms import VisitForm
from models import *

class VisitAdmin(admin.ModelAdmin):
    search_fields = ['description']
    list_display = ('beamline', 'proposal_display','description','notify', 'start_date', 'first_shift', 'end_date', 'last_shift','remote','mail_in','maintenance','purchased')
    form = VisitForm
    fieldsets = (
        (None, {
            'fields': ('beamline', 'proposal', ('remote','mail_in','maintenance','purchased'), 'description', ('start_date', 'first_shift'), ('end_date', 'last_shift'),'notify'), 
        }),
    )

class ProposalAdmin(admin.ModelAdmin):
    list_display = ('__unicode__','last_name','proposal_id','email','expiration','account')
    list_filter = ('expiry',)

class OnCallAdmin(admin.ModelAdmin):
    search_fields = ['local_contact', 'date']
    list_display = ('date','local_contact')

class SupportPersonAdmin(admin.ModelAdmin):
    list_display = ('last_name','first_name','phone_number','category','office')

class StatAdmin(admin.ModelAdmin):
    list_display = ('mode','start_date','first_shift','end_date','last_shift')

class WebStatusAdmin(admin.ModelAdmin):
    list_display = ('date','status1','status2','status3')

admin.site.register(Beamline)
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(SupportPerson, SupportPersonAdmin)
admin.site.register(Visit, VisitAdmin)
admin.site.register(OnCall, OnCallAdmin)
admin.site.register(Stat, StatAdmin)
admin.site.register(WebStatus, WebStatusAdmin)