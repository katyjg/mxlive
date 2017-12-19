from django.apps import AppConfig
from django.conf import settings

class StaffConfig(AppConfig):
    name = 'staff'
    verbose_name = "{} Staff".format(getattr(settings, "APP_LABEL", 'App'))