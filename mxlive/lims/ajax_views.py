import os
import re
import pickle
import urlparse
from django.views.generic import View
from django import http
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

import numpy
import requests
from PIL import Image
from django.conf import settings
from django.http import JsonResponse

from imageio import read_image
from imageio.utils import stretch
from lims import models

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
COLORMAPS = pickle.load(file(os.path.join(DATA_DIR, 'colormaps.data')))

BRIGHTNESS_VALUES = getattr(settings, 'DOWNLOAD_BRIGHTNESS_VALUES', {'xl': -1.5, 'nm': 0.0, 'dk': 1.5, 'lt': -0.5})

# Modify default colormap to add overloaded pixel effect
COLORMAPS['gist_yarg'][-1] = 0
COLORMAPS['gist_yarg'][-2] = 0
COLORMAPS['gist_yarg'][-3] = 255
GAMMA_SHIFT = 3.5

IMAGE_URL = settings.IMAGE_PREPEND or ''
CACHE_DIR = settings.CACHES.get('default', {}).get('LOCATION', '/tmp')


def load_image(filename, gamma_offset=0.0, resolution=(1024, 1024)):
    """
    Read file and return an PIL image of desired resolution histogram stretched by the
    requested gamma_offset
    :param filename: Image File (e.g. filename.img, filename.cbf)
    :param gamma_offset: default 0.0
    :param resolution: output size
    :return: resized PIL image
    """

    image_obj = read_image(filename)
    gamma = image_obj.header['gamma']
    disp_gamma = gamma * numpy.exp(gamma_offset + GAMMA_SHIFT)/30.0
    raw_img = image_obj.image.convert('I')
    lut = stretch(disp_gamma)
    raw_img = raw_img.point(list(lut), 'L')
    raw_img.putpalette(COLORMAPS['gist_yarg'])
    return raw_img.resize(resolution, Image.ANTIALIAS)  # slow but nice Image.NEAREST is very fast but ugly


def create_png(filename, output, brightness, resolution=(1024, 1024)):
    """
    Generate png in output using filename as input with specified brightness
    and resolution. default resolution is 1024x1024
    creates a directory for output if none exists
    :param filename: Image File (e.g. filename.img, filename.cbf)
    :param output: PNG Image Filename
    :param brightness: float (1.5=dark; -0.5=light)
    :param resolution: output size
    :return: PNG Image
    """

    img_info = load_image(filename, brightness, resolution)

    dir_name = os.path.dirname(output)
    if not os.path.exists(dir_name) and dir_name != '':
        os.makedirs(dir_name)
    img_info.save(output, 'PNG')


@method_decorator(csrf_exempt, name='dispatch')
class FetchReport(View):

    def get(self, request, *args, **kwargs):
        try:
            report = models.AnalysisReport.objects.get(pk=kwargs.get('pk'))
        except models.AnalysisReport.DoesNotExist:
            raise http.Http404("Report does not exist.")

        if report.project != request.user and not request.user.is_superuser:
            raise http.Http404()

        return JsonResponse({'details': report.details}, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class UpdatePriority(View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        try:
            group = models.Group.objects.get(pk=request.POST.get('group'))
        except models.Group.DoesNotExist:
            raise http.Http404("Group does not exist.")

        if group.project != request.user:
            raise http.Http404()

        pks = [u for u in request.POST.getlist('samples[]') if u]
        for i, pk in enumerate(pks):
            group.sample_set.filter(pk=pk).update(priority=i+1)

        return JsonResponse([], safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class BulkSampleEdit(View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        errors = []

        group = request.POST.get('group')
        if models.Group.objects.get(pk=group).project.username != self.request.user.username:
            errors.append('You do not have permission to modify these samples.')
            return JsonResponse(errors, safe=False)

        data = {}
        i = 0
        while request.POST.getlist('samples[{}][]'.format(i)):
            info = request.POST.getlist('samples[{}][]'.format(i))
            data[info[0]] = {'name': info[1], 'barcode': info[2], 'comments': info[3]}
            i += 1

        for name in set([v['name'] for v in data.values()]):
            if not re.compile('^[a-zA-Z0-9-_]+$').match(name):
                errors.append('{}: Names cannot contain any spaces or special characters'.format(name.encode('utf-8')))

        names = list(models.Sample.objects.filter(group__pk=group).exclude(pk__in=data.keys()).values_list('name', flat=True))
        names.extend([v['name'] for v in data.values()])

        duplicates = set([name for name in names if names.count(name) > 1])
        for name in duplicates:
            errors.append('{}: Each sample in the group must have a unique name'.format(name))

        if not errors:
            for pk, info in data.items():
                models.Sample.objects.filter(pk=pk).update(**info)

        return JsonResponse(errors, safe=False)

def update_locations(request):
    container = models.Container.objects.get(pk=request.GET.get('pk', None))
    locations = list(container.kind.container_locations.values_list('pk', 'name'))
    return JsonResponse(locations, safe=False)


def fetch_image(request, url=None, brightness=None):
    src = ""
    url = url or request.GET.get('url', None)
    brightness = brightness or request.GET.get('brightness', 'nm')
    if url:
        img_file = '/'.join([CACHE_DIR] + url.split('/')[-2:])
        path, _ = os.path.splitext(img_file)
        png_file = "{}-{}.png".format(path, brightness)
        if not os.path.isfile(png_file):
            r = requests.get(url)
            if r.status_code == 200:
                if not os.path.exists(path):
                    os.makedirs(path)
                with open(img_file, 'w') as f:
                    f.write(r.content)
                if not os.path.exists(png_file):
                    try:
                        create_png(img_file, png_file, BRIGHTNESS_VALUES[brightness])
                        os.remove(img_file)
                    except OSError:
                        pass
        src = "/cache{}".format(png_file.replace(CACHE_DIR, ""))

    return JsonResponse({'src': src})


def fetch_file(request, url=None):
    url = url or request.GET.get('url', None)
    src = ''
    if url:
        f = '/'.join([CACHE_DIR] + url.split('/')[-2:])
        path, _ = os.path.splitext(f)
        if not os.path.isfile(f):
            r = requests.get(url)
            if r.status_code == 200:
                path, file_extension = os.path.splitext(f)
                if not os.path.exists(path):
                    os.makedirs(path)

                with open(f, 'w') as cached_file:
                    cached_file.write(r.content)
        src = "/cache{}".format(f.replace(CACHE_DIR, ""))
    return JsonResponse({'src': src})


def fetch_archive(request, path=None, name=None):
    if path:
        url = IMAGE_URL + "/files/{}/{}".format(path, name)
        r = requests.get(url, stream=True)
    else:
        url = IMAGE_URL + "/files/{}?{}".format(name, request.GET.urlencode())
        r = requests.get(url, stream=True)

    if 'tar.gz' in name:
        resp = http.StreamingHttpResponse(r, content_type='application/x-gzip')
        resp['Content-Disposition'] = 'attachment; filename={0}'.format(name)
    else:
        resp = http.HttpResponse(r)
    return resp
