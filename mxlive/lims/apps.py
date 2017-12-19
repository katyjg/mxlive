from django.apps import AppConfig
from django.conf import settings


class LimsConfig(AppConfig):
    name = 'lims'
    verbose_name = "{} Users".format(getattr(settings, "APP_LABEL", 'App'))