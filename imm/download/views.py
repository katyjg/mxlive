from django.conf import settings
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views.static import serve
import re
import posixpath
import urllib
import os

from download.models import SecurePath
from download.frameconverter import create_png
from download.maketarball import create_tar

KEY_RE = re.compile('^[a-f0-9]{40}$')
CACHE_DIR = getattr(settings, 'DOWNLOAD_CACHE_DIR', '/tmp')
BRIGHTNESS_VALUES = getattr(settings, 'DOWNLOAD_BRIGHTNESS_VALUES', {'nm': 0.0, 'dk': -0.5, 'lt': 1.5})
FRONTEND = getattr(settings, 'DOWNLOAD_FRONTEND', 'xsendfile')

def create_download_key(path):
    """Convenience method to create and return a key for a given path"""

    obj = SecurePath()
    obj.path = path
    obj.save()
    return obj.key

def get_download_path(key):
    """Convenience method to return a path for a key"""
    
    obj = SecurePath.objects.get(key=key)
    return obj.path


def send_file(request, full_path, attatchment=False):
    """Send a file using mod_xsendfile or similar functionality. 
    Use django's static serve option for development servers"""
    
    if not os.path.exists(full_path):
        raise Http404
    
    if FRONTEND == "xsendfile":
        response = HttpResponse()
        response['X-Sendfile'] = full_path
        if attatchment:
            response['Content-Disposition'] = 'attatchment; filename=%s' % os.path.basename(full_path)
        # Unset the Content-Type as to allow for the webserver
        # to determine it.
        response['Content-Type'] = ''
    elif FRONTEND == "django":
        dirname = os.path.dirname(full_path)
        path = os.path.basename(full_path)
        print "Serving file %s in directory %s through django static serve." % (path, dirname)
        response = serve(request, path, dirname)
        
    elif FRONTEND == "xaccelredirect":
        response = HttpResponse()
        response['X-Accel-Redirect'] = full_path
        if attatchment:
            response['Content-Disposition'] = 'attatchment; filename=%s' % os.path.basename(full_path)
        response['Content-Type'] = ''
        response = HttpResponse()
        # FIXME: find out how to use wsgi.file_wrapper as a frontend as well
        
    return response

def send_image(request, key, path):

    obj = get_object_or_404(SecurePath, key=key)
    document_root = obj.path
    
    # Clean up given path to only allow serving files below document_root.
    path = posixpath.normpath(urllib.unquote(path))
    path = path.lstrip('/')
    newpath = ''
    for part in path.split('/'):
        if not part:
            # Strip empty path components.
            continue
        drive, part = os.path.splitdrive(part)
        head, part = os.path.split(part)
        if part in (os.curdir, os.pardir):
            # Strip '.' and '..' in path.
            continue
        newpath = os.path.join(newpath, part).replace('\\', '/')
    if newpath and path != newpath:
        return HttpResponseRedirect(newpath)
    full_path = os.path.join(document_root, newpath)
    print full_path, os.path.exists(full_path)
    
    return send_file(request, full_path)
    
def send_png(request, key, path, brightness):
    if brightness not in BRIGHTNESS_VALUES:
        raise Http404
    
    obj = get_object_or_404(SecurePath, key=key)
    img_file = os.path.join(obj.path, '%s.img' % path)
    png_file = os.path.join(CACHE_DIR, obj.key, '%s-%s.png' % (path, brightness))
    if not os.path.exists(png_file):
        try:
            create_png(img_file, png_file, BRIGHTNESS_VALUES[brightness])
        except OSError:
            raise Http404        
    return send_file(request, png_file, attatchment=False)

def send_archive(request, key, path):

    obj = get_object_or_404(SecurePath, key=key)
    dir_name = os.path.join(obj.path, path)
    tar_file = os.path.join(CACHE_DIR, obj.key, '%s.tar.gz' % (path,))
    if not os.path.exists(tar_file):
        try:
            create_tar(dir_name, tar_file)
        except OSError:
            raise Http404        
    return send_file(request, tar_file, attatchment=True)   