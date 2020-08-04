from django.contrib import admin
from mxlive.lims import models


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('identity', 'project')
    search_fields = ('name', 'project')


class UserAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email')
    search_fields = ('name', 'contact_person')

class LocationAdmin(admin.ModelAdmin):
    list_filter = ('kind',)

admin.site.register(models.Guide)
admin.site.register(models.Beamline)
admin.site.register(models.Dewar)
admin.site.register(models.ProjectType)
admin.site.register(models.ProjectDesignation)
admin.site.register(models.Project, UserAdmin)
admin.site.register(models.ComponentType)
admin.site.register(models.DataType)
admin.site.register(models.ContainerType)
admin.site.register(models.ContainerLocation, LocationAdmin)

admin.site.register(models.Shipment, ProjectAdmin)
admin.site.register(models.Container, ProjectAdmin)
admin.site.register(models.Group, ProjectAdmin)
admin.site.register(models.Sample, ProjectAdmin)
admin.site.register(models.Data, ProjectAdmin)
admin.site.register(models.AnalysisReport, ProjectAdmin)
admin.site.register(models.Session, ProjectAdmin)

admin.site.register(models.FeedbackScale)
admin.site.register(models.SupportArea)
admin.site.register(models.UserFeedback)
admin.site.register(models.SupportRecord)