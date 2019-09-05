import os
import time

from django import template
from django.conf import settings

register = template.Library()


@register.filter("get_version")
def get_version(val=None):
    return time.strftime('%Y.%d.%m', time.gmtime(os.path.getmtime('../..')))


@register.filter("get_from_settings")
def get_from_settings(val=None):
    return getattr(settings, val, '')
