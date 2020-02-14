from django.contrib import admin
from mxlive.schedule import models


admin.site.register(models.BeamlineProject)
admin.site.register(models.Beamtime)
admin.site.register(models.AccessType)
