
from .frameconverter import create_png
from .maketarball import create_tar
from .models import SecurePath
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.static import serve
from lims.models import Data
import os
import posixpath
import re
import subprocess
import urllib
import zipstream
from django.http import StreamingHttpResponse

KEY_RE = re.compile('^[a-f0-9]{40}$')
CACHE_DIR = getattr(settings, 'DOWNLOAD_CACHE_DIR', '/tmp')
RESTRICTED_DOWNLOADS = getattr(settings, 'RESTRICTED_DOWNLOADS', True)
BRIGHTNESS_VALUES = getattr(settings, 'DOWNLOAD_BRIGHTNESS_VALUES', {'nm': 0.0, 'dk': -0.5, 'lt': 1.5})
FRONTEND = getattr(settings, 'DOWNLOAD_FRONTEND', 'xsendfile')
USER_ROOT = getattr(settings, 'LDAP_USER_ROOT', '/users')
ROOT_RE = re.compile('^{}'.format(USER_ROOT))

def create_cache_dir(key):
    dir_name = os.path.join(CACHE_DIR, key)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name
    
def create_download_key(path, owner_id):
    """Convenience method to create and return a key for a given path"""

    obj = SecurePath()
    obj.path = re.sub(ROOT_RE, "/users", path)
    obj.owner_id = owner_id
    obj.save()
    return obj.key

def get_download_path(key):
    """Convenience method to return a path for a key"""
    
    obj = SecurePath.objects.get(key=key)
    return obj.path


def send_raw_file(request, full_path, attachment=False):
    """Send a file using mod_xsendfile or similar functionality. 
    Use django's static serve option for development servers"""

    if not os.path.exists(full_path):
        raise Http404

    if FRONTEND == "xsendfile":
        response = HttpResponse()
        response['X-Sendfile'] = full_path
        if attachment:
            response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(full_path)
        # Unset the Content-Type as to allow for the webserver
        # to determine it.
        response['Content-Type'] = ''

    elif FRONTEND == "xaccelredirect":
        response = HttpResponse()
        response['X-Accel-Redirect'] = full_path
        if attachment:
            response['Content-Disposition'] = 'attachment; filename=%s' % os.path.basename(full_path)
        response['Content-Type'] = ''
        response = HttpResponse()
    else:
        dirname = os.path.dirname(full_path)
        path = os.path.basename(full_path)
        #"Serving file %s in directory %s through django static serve." % (path, dirname)
        response = serve(request, path, dirname)

    return response

@login_required
def send_file(request, key, path):

    obj = get_object_or_404(SecurePath, key=key)
    
    # make sure only owner and staff can get their files
    if not request.user.is_staff:
        if request.user.get_profile() != obj.owner:
            raise Http404
    
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
    return send_raw_file(request, full_path)


@login_required   
def send_png(request, key, path, brightness):
    if brightness not in BRIGHTNESS_VALUES:
        raise Http404
    
    obj = get_object_or_404(SecurePath, key=key)
    # make sure only owner and staff can get their files
    if not request.user.is_staff:
        if request.user.get_profile() != obj.owner:
            return HttpResponseRedirect('/static/img/image-not-found.png')

    img_file = os.path.join(obj.path, path)
    png_file = os.path.join(CACHE_DIR, obj.key, '%s-%s.png' % (path, brightness))

    if not os.path.exists(png_file):
        try:
            create_png(img_file, png_file, BRIGHTNESS_VALUES[brightness])
        except OSError:
            return HttpResponseRedirect('/static/img/image-not-found.png')
            #raise Http404        
    return send_raw_file(request, png_file, attachment=False)

@login_required
def find_file(request, pk, path):
    data = Data.objects.get(pk=pk)
    obj = get_object_or_404(SecurePath, key=data.url)
    if not request.user.is_staff:
        if request.user.get_profile() != obj.owner:
            return HttpResponseRedirect('/static/img/sample-not-found.png')

    if os.path.exists(get_download_path(obj.key)):
        filename = os.path.join(CACHE_DIR, obj.key, '%s.gif' % path)
        png_path = "%s/%s-pic_*.png" % (get_download_path(obj.key), data.name)
        create_cache_dir('%s/%s' % (CACHE_DIR, obj.key))
        command = 'convert -delay 200 -resize 300x {0} {1}'.format(png_path, filename)
        try:
            subprocess.check_call(command.split())
        except:
            try:
                subprocess.check_call(command.replace('_test-pic','-pic').split())
            except:
                return HttpResponseRedirect('/static/img/sample-not-found.png')
    
    return send_raw_file(request, filename, attachment=False)

@login_required
def send_archive_old(request, key, path, data_dir=False): #Add base parameter and another url

    obj = get_object_or_404(SecurePath, key=key)
    # make sure only owner and staff can get their files
    if not request.user.is_staff:
        if request.user.get_profile() != obj.owner:
            raise Http404
    if data_dir:
        # make sure downloading is enabled for this dataset
        data = get_object_or_404(Data, url=key, name=path, download=True)
    
    tar_file = os.path.join(CACHE_DIR, obj.key, '%s.tar.gz' % (path,))
    if not os.path.exists(tar_file):
        try:
            create_tar(obj.path, tar_file, data_dir=data_dir)
        except OSError:
            raise Http404        
    return send_raw_file(request, tar_file, attachment=True)


@login_required
def send_archive2(request, key, path, data_dir=False):  # Add base parameter and another url
    obj = get_object_or_404(SecurePath, key=key)
    # make sure only owner and staff can get their files
    if not request.user.is_superuser:
        if not (request.user.get_profile() == obj.owner):
            raise Http404
    if data_dir and RESTRICTED_DOWNLOADS:
        # make sure downloading is enabled for this dataset
        get_object_or_404(Data, url=key, name=path, download=True)

    if os.path.exists(obj.path):
        z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED, allowZip64=True)
        for root, dirs, files in os.walk(obj.path):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcpath = os.path.join(path, os.path.relpath(file_path, obj.path))
                z.write(file_path, arcpath)
        response = StreamingHttpResponse(z, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename={}.zip'.format(path)
        return response
    else:
        raise Http404


@login_required
def send_archive(request, key, path, data_dir=False):  # Add base parameter and another url
    obj = get_object_or_404(SecurePath, key=key)
    # make sure only owner and staff can get their files
    if not request.user.is_superuser:
        if not (request.user.get_profile() == obj.owner):
            raise Http404
    if data_dir and RESTRICTED_DOWNLOADS:
        # make sure downloading is enabled for this dataset
        get_object_or_404(Data, url=key, name=path, download=True)

    if os.path.exists(obj.path):
        p = subprocess.Popen(
            ['tar', '-czf', '-', os.path.basename(obj.path)],
            cwd=os.path.dirname(obj.path),
            stdout=subprocess.PIPE
        )
        response = StreamingHttpResponse(p.stdout, content_type='application/x-gzip')
        response['Content-Disposition'] = 'attachment; filename={}.tar.gz'.format(path)
        return response
    else:
        raise Http404

