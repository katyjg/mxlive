import os
import pickle
import urlparse

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
        if not os.path.exists(png_file):
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
        if not os.path.exists(f):
            r = requests.get(url)
            if r.status_code == 200:
                path, file_extension = os.path.splitext(f)
                if not os.path.exists(path):
                    os.makedirs(path)

                with open(f, 'w') as cached_file:
                    cached_file.write(r.content)
        src = "/cache{}".format(f.replace(CACHE_DIR, ""))
    return JsonResponse({'src': src})
