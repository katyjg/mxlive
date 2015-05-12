from django.contrib import admin

from scheduler import models

class VisitAdmin(admin.ModelAdmin):
    search_fields = ['description']
    list_display = ('beamline', 'proposal_display','description','notify', 'start_date', 'first_shift', 'end_date', 'last_shift','remote','mail_in','maintenance','purchased')
    fieldsets = (
        (None, {
            'fields': ('beamline', 'proposal', ('remote','mail_in','maintenance','purchased'), 'description', ('start_date', 'first_shift'), ('end_date', 'last_shift'),'notify'), 
        }),
    )

class ProposalAdmin(admin.ModelAdmin):
    list_display = ('__unicode__','last_name','proposal_id','email','expiration','account')
    list_filter = ('expiration',)

class OnCallAdmin(admin.ModelAdmin):
    search_fields = ['local_contact', 'date']
    list_display = ('date','local_contact')

class SupportPersonAdmin(admin.ModelAdmin):
    list_display = ('last_name','first_name','phone_number','category','office')

class StatAdmin(admin.ModelAdmin):
    list_display = ('mode','start_date','first_shift','end_date','last_shift')

admin.site.register(models.Beamline)
admin.site.register(models.Proposal, ProposalAdmin)
admin.site.register(models.SupportPerson, SupportPersonAdmin)
admin.site.register(models.Visit, VisitAdmin)
admin.site.register(models.OnCall, OnCallAdmin)
admin.site.register(models.Stat, StatAdmin)
