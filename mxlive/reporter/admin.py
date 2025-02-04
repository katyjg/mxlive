from django.contrib import admin
from . import models


admin.site.register(models.DataModel)
admin.site.register(models.DataSource)
admin.site.register(models.DataField)
admin.site.register(models.Report)
admin.site.register(models.Entry)

