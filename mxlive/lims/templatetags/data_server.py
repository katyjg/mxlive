import collections
import json

import requests
from django import template
from django.conf import settings
from django.urls import reverse

from mxlive.utils import xdi

GOOG20_COLORS = [
    "#3366cc", "#dc3912", "#ff9900", "#109618", "#990099", "#0099c6", "#dd4477", "#66aa00", "#b82e2e",
    "#316395", "#994499", "#22aa99", "#aaaa11", "#6633cc", "#e67300", "#8b0707", "#651067", "#329262",
    "#5574a6", "#3b3eac"
]
PROXY_URL = getattr(settings, 'DOWNLOAD_PROXY_URL', "http://mxlive-data/download")

register = template.Library()


@register.simple_tag
def get_frame_name(data, frame):
    return data.file_name.format(frame)


@register.simple_tag
def get_frame_url(data, frame):
    return '{}/{}'.format(data.url, data.file_name.format(frame))


@register.filter
def format_frame_name(data, frame):
    return data.file_name.format(frame)


@register.filter("second_view")
def second_view(angle):
    if angle:
        return float(angle) < 270 and float(angle) + 90 or float(angle) - 270
    return angle


@register.filter
def get_meta_data(data):
    return collections.OrderedDict(
        [(k, data.meta_data.get(k)) for k in data.METADATA[data.kind] if k in data.meta_data])


def get_json_info(path):
    url = PROXY_URL + reverse('files-proxy', kwargs={'section': 'raw', 'path': path})
    r = requests.get(url)
    if r.status_code == 200:
        return json.loads(r.content)
    else:
        print("File not found: {}".format(path))
        return {}


def get_xdi_info(path):
    url = PROXY_URL + reverse('files-proxy', kwargs={'section': 'raw', 'path': path})
    r = requests.get(url)
    if r.status_code == 200:
        return xdi.read_xdi_data(r.content)
    else:
        print("File not found: {}".format(url))
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
            'choices': [dict((str(k), isinstance(v, str) and str(v) or v) for k, v in choice.items())
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
                    'x': analysis.get('energy', []),
                    'y1': analysis.get('fit', [])},
            ],
            'assignments': sorted(assignments, key=lambda x: -x['reliability'])
        }
        for i, a in enumerate(info['assignments']):
            info['assignments'][i]['color'] = GOOG20_COLORS[i % 20]
    else:
        info = {'assignments': [], 'data': []}
    return info
