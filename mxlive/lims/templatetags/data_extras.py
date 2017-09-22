from django.template import Library
from download.views import get_download_path
import os
import collections

register = Library()

@register.simple_tag
def image_url(data, frame, brightness=None):
    try:
        ret_val = data.generate_image_url(frame, brightness)
    except:
        return ""
    return ret_val

@register.filter("is_downloadable")
def is_downloadable(data, frame):
    path = "%s/%s_%04d%s" % (get_download_path(data.url), data.name, frame, data.file_extension())
    return os.path.exists(path)

@register.filter("second_view")
def second_view(angle):
    return angle < 270 and angle + 90 or angle - 270

@register.filter
def get_meta_data(data):
    return collections.OrderedDict([(k, data.meta_data[k]) for k in data.METADATA[data.kind]])
    return {k: data.meta_data[k] for k in data.METADATA[data.kind]}