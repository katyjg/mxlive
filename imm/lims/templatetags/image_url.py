from django import template
from django.template import Library
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateformat
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import get_date_formats
from django.contrib import admin
from django.conf import settings 
from django.utils.safestring import mark_safe
from django.utils.datastructures import MultiValueDict

from imm.lims.models import Data
from imm.download.views import get_download_path
import os    

register = Library()

import logging

@register.simple_tag
def image_url(data, frame, brightness=None):
    ret_val = data.generate_image_url(frame, brightness)
    return ret_val

@register.filter("is_downloadable")
def is_downloadable(data, frame):
    path = "%s/%s_%03d.img" % (get_download_path(data.url), data.name, frame)
    return os.path.exists(path)
