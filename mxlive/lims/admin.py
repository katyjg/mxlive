from django.contrib import admin
from lims.models import *

admin.site.register(Beamline)
admin.site.register(Project)
admin.site.register(Shipment)
admin.site.register(ComponentType)
admin.site.register(Container)
admin.site.register(Sample)
admin.site.register(Data)
admin.site.register(AnalysisReport)
admin.site.register(ScanResult)
admin.site.register(ContainerType)
admin.site.register(ContainerLocation)
admin.site.register(Dewar)
