import os
import time

from django.conf import settings
from django.shortcuts import get_object_or_404
from django import template  

from imm.download.models import SecurePath

register = template.Library()  

CACHE_DIR = getattr(settings, 'DOWNLOAD_CACHE_DIR', '/tmp')

@register.filter("file_exists")  
def file_exists(data, ext):
    obj = get_object_or_404(SecurePath, key=data.url)
    file = os.path.join(CACHE_DIR, obj.key, '%s.%s' % (data.name, ext))
    return os.path.exists(file)

@register.filter("file_updated")
def file_updated(data, ext):
    obj = get_object_or_404(SecurePath, key=data.url)
    file = os.path.join(CACHE_DIR, obj.key, '%s.%s' % (data.name, ext))
    return (time.time() - os.path.getmtime(file)) < 120
    
    
@register.filter("get_size")
def get_size(data):
    try:
        obj = get_object_or_404(SecurePath, key=data.url)
        tar_file = os.path.join(CACHE_DIR, obj.key, '%s.tar.gz' % data.name)
        size = os.path.getsize(tar_file)
        if size >= 1e9:   parsed = 'quite large (%0.4gGb)' % float(size/1e9)
        elif size >= 1e6: parsed = 'large (%0.4gMb)' % float(size/1e6)
        elif size >= 1e3: parsed = '%0.4gKb' % float(size/1e3)
        else:             parsed = '%0.4gb' % float(size)
    except:
        parsed = 'of unknown size'
    return parsed
    
@register.filter("get_adj")
def get_adj(string):
    if string.find('G') != -1:   adj = 'a very long time'
    elif string.find('M') != -1: adj = 'awhile'
    else: adj = 'a few minutes'
    return adj
    