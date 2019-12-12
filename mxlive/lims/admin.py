from django.contrib import admin
from mxlive.lims import models


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('identity', 'project')
    search_fields = ('identity', 'project')


admin.site.register(models.Beamline)
admin.site.register(models.Dewar)
admin.site.register(models.Project)
admin.site.register(models.ComponentType)
admin.site.register(models.DataType)
admin.site.register(models.ContainerType)
admin.site.register(models.ContainerLocation)


admin.site.register(models.Shipment, ProjectAdmin)
admin.site.register(models.Container, ProjectAdmin)
admin.site.register(models.Group, ProjectAdmin)
admin.site.register(models.Sample, ProjectAdmin)
admin.site.register(models.Data, ProjectAdmin)
admin.site.register(models.AnalysisReport, ProjectAdmin)
admin.site.register(models.Session, ProjectAdmin)

