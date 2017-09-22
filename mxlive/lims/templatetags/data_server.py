from django import template
from django.conf import settings

from lims.ajax_views import fetch_image
import json

register = template.Library()

IMAGE_URL = settings.IMAGE_PREPEND or ''


@register.simple_tag
def get_image_url(data, frame):
    url = IMAGE_URL + "/files/%s/%s_%04d%s" % (data.url, data.name, frame, data.file_extension())
    return url


@register.simple_tag
def get_image(data, frame, brightness="nm"):
    url = IMAGE_URL + "/files/%s/%s_%04d%s" % (data.url, data.name, frame, data.file_extension())
    info = fetch_image(None, url, brightness)
    src = json.loads(info.content)['src']
    return src
