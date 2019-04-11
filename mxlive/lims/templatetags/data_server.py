from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

import json
import xdi
import collections
import requests
import os
import matplotlib.pyplot as plt

XRF_COLOR_LIST = ['#800080', '#FF0000', '#008000',
                  '#FF00FF', '#800000', '#808000',
                  '#008080', '#00FF00', '#000080',
                  '#00FFFF', '#0000FF', '#000000',
                  '#800040', '#BD00BD', '#00FA00',
                  '#800000', '#FA00FA', '#00BD00',
                  '#008040', '#804000', '#808000',
                  '#408000', '#400080', '#004080']


def get_color(i):
    color = plt.cm.gnuplot(i)
    return '#%02x%02x%02x' % (color[0]*255, color[1]*255, color[2]*255)


register = template.Library()

IMAGE_URL = settings.IMAGE_PREPEND or ''
CACHE_DIR = settings.CACHES.get('default', {}).get('LOCATION', '/tmp')
CACHE_URL = settings.CACHE_URL or '/cache/'


@register.simple_tag
def get_frame_name(data, frame):
    return data.file_name.format(frame)

@register.simple_tag
def get_frame_url(data, frame):
    return '{}/{}'.format(data.url, data.file_name.format(frame))

@register.filter
def format_frame_name(data, frame):
    return data.file_name.format(frame)


@register.simple_tag
def get_cached_image_url(data, frame, brightness='nm'):
    file_name, _ = os.path.splitext(data.file_name.format(frame))
    return "{}/{}/{}-{}.png".format(CACHE_URL, data.url, file_name, brightness)


@register.simple_tag
def get_base_url(data):
    return IMAGE_URL + "/files/{}/".format(data.url)


@register.filter("second_view")
def second_view(angle):
    if angle:
        return float(angle) < 270 and float(angle) + 90 or float(angle) - 270
    return angle


@register.filter
def get_meta_data(data):
    return collections.OrderedDict([(k, data.meta_data.get(k)) for k in data.METADATA[data.kind] if k in data.meta_data])


def get_json_info(path):
    url = IMAGE_URL + reverse('files-proxy', kwargs={'section': 'raw', 'path': path})
    r = requests.get(url)
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        print "File not found: {}".format(path)
        return {}


def get_xdi_info(path):
    url = IMAGE_URL + reverse('files-proxy', kwargs={'section': 'raw', 'path': path})
    r = requests.get(url)
    if r.status_code == 200:
        return xdi.read_xdi_data(r.content)
    else:
        print "File not found: {}".format(url)
        return {}


@register.simple_tag
def get_mad_data(data):
    xdi_path = '{}/{}'.format(data.url, data.file_name)
    mad_path = '{}/{}.mad'.format(data.url, data.name)
    raw = get_xdi_info(xdi_path)
    analysis = get_json_info(mad_path)
    if raw and analysis:
        info = {
            'xlabel': 'Energy ({})'.format(raw['column.1'].units),
            'y1label': 'Fluorescence Counts',
            'y2label': 'Anomalous Scattering Factors (f`, f``)',
            'data': [
                {
                    'label': '',
                     'x': list(raw.data['energy']),
                     'y1': list(raw.data['normfluor'])},
                {
                    'label': 'f`',
                     'x': analysis['esf']['energy'],
                     'y2': analysis['esf']['fp']},
                {
                    'label': 'f``',
                     'x': analysis['esf']['energy'],
                     'y2': analysis['esf']['fpp']},
            ],
            'choices': [dict((str(k), isinstance(v, unicode) and str(v) or v) for k, v in choice.items())
                        for choice in analysis['choices']]
        }
    else:
        info = {'choices': [], 'data': []}
    return info


@register.simple_tag
def get_xrf_data(data):
    xdi_path = '{}/{}'.format(data.url, data.file_name)
    xrf_path = '{}/{}.xrf'.format(data.url, data.name)
    raw = get_xdi_info(xdi_path)
    analysis = get_json_info(xrf_path)
    if analysis:
        assignments = [{
            'label': str(el),
            'reliability': values[0],
            'edges': [{
                'label': "{}-{}".format(el, edge[0]),
                'energy': edge[1],
                'amplitude': edge[2]
                } for edge in values[1]]
            }
            for el, values in analysis.get('assignments', {}).items()]
        info = {
            'xlabel': 'Energy ({})'.format(raw['column.1'].units),
            'y1label': 'Fluorescence Counts',
            'data': [
                {
                    'label': 'Counts',
                    'x': analysis.get('energy', []),
                    'y1': analysis.get('counts', [])},
                {
                    'label': 'Fit',
                    'x': analysis.get('energy',[]),
                    'y1': analysis.get('fit',[])},
            ],
            'assignments': sorted(assignments, key=lambda x: -x['reliability'])
        }
        for i, a in enumerate(info['assignments']):
            info['assignments'][i]['color'] = get_color(i*12)
    else:
        info = {'assignments': [], 'data': []}
    return info

