from django.http import JsonResponse
from django.conf import settings

from lims import models
from download.imageio import read_image, read_header
from download.imageio.utils import stretch

import requests
import os
import numpy
import urlparse
import pickle
from PIL import Image

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
COLORMAPS = pickle.load(file(os.path.join(DATA_DIR, 'colormaps.data')))

BRIGHTNESS_VALUES = getattr(settings, 'DOWNLOAD_BRIGHTNESS_VALUES', {'nm': 0.0, 'dk': 1.5, 'lt': -0.5})

# Modify default colormap to add overloaded pixel effect
COLORMAPS['gist_yarg'][-1] = 0
COLORMAPS['gist_yarg'][-2] = 0
COLORMAPS['gist_yarg'][-3] = 255
GAMMA_SHIFT = 3.5

IMAGE_URL = settings.IMAGE_PREPEND or ''
CACHE_DIR = settings.CACHES.get('default', {}).get('LOCATION', '/tmp')


def load_image(filename, gamma_offset=0.0, resolution=(1024, 1024)):
    # Read file and return an PIL image of desired resolution histogram stretched by the
    # requested gamma_offset

    image_obj = read_image(filename)
    gamma = image_obj.header['gamma']
    disp_gamma = gamma * numpy.exp(gamma_offset + GAMMA_SHIFT)/30.0
    raw_img = image_obj.image.convert('I')
    lut = stretch(disp_gamma)
    raw_img = raw_img.point(list(lut), 'L')
    raw_img.putpalette(COLORMAPS['gist_yarg'])
    return raw_img.resize(resolution, Image.ANTIALIAS)  # slow but nice Image.NEAREST is very fast but ugly


def create_png(filename, output, brightness, resolution=(1024, 1024)):
    # generate png in output using filename as input with specified brightness
    # and resolution. default resolution is 1024x1024
    # creates a directory for output if none exists

    img_info = load_image(filename, brightness, resolution)

    dir_name = os.path.dirname(output)
    if not os.path.exists(dir_name) and dir_name != '':
        os.makedirs(dir_name)
    img_info.save(output, 'PNG')


def update_locations(request):
    container = models.Container.objects.get(pk=request.GET.get('pk', None))
    locations = list(container.kind.container_locations.values_list('pk', 'name'))
    return JsonResponse(locations, safe=False)


def get_image(data, frame, brightness="nm"):
    url = IMAGE_URL + "/images/%s/%s_%04d%s" % (data.url, data.name, frame, data.file_extension())
    return fetch_image(None, url, brightness)


def fetch_image(request, url=None, brightness=None):
    url = url or request.GET.get('url', None)
    brightness = brightness or request.GET.get('brightness', 'nm')
    if url:
        r = requests.get(url)
        if r.status_code == 200:
            img_file = ''.join([CACHE_DIR, urlparse.urlparse(r.url).path])
            path, file_extension = os.path.splitext(img_file)
            png_file = "{}-{}.png".format(path, brightness)
            if not os.path.exists(path):
                os.makedirs(path)
            with open(img_file, 'w') as f:
                f.write(r.content)

            if not os.path.exists(png_file):
                try:
                    create_png(img_file, png_file, BRIGHTNESS_VALUES[brightness])
                except OSError:
                    return JsonResponse({'src': ''})
            return JsonResponse({'src': "/cache{}".format(png_file.replace(CACHE_DIR, ""))})
    return JsonResponse({'src':''})
