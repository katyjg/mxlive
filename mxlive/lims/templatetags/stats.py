from django import template
from django.utils.safestring import mark_safe

from lims.models import *
from converter import humanize_duration

from collections import defaultdict
import json

register = template.Library()


@register.assignment_tag(takes_context=False)
def get_data_stats(bl):
    table = summarize_activity(Data.objects.filter(beamline=bl))
    stats = {'details': [
        {
            'title': '{} Statistics'.format(bl.acronym),
            'description': 'Data Collection Summary for {}'.format(bl.name),
            'style': "col-xs-12",
            'content': [
                {
                    'title': '',
                    'kind': 'table',
                    'data': table,
                    'header': 'row'
                },
            ]
        }
    ]}
    return mark_safe(json.dumps(stats))


@register.assignment_tag(takes_context=False)
def get_session_stats(data, session):
    table = [[k for k, _ in Data.DATA_TYPES], [data.filter(kind=k).count() for k, _ in Data.DATA_TYPES]]
    stats = {'details': [
        {
            'title': 'Session Statistics',
            'description': 'Data Collection Summary',
            'style': "col-xs-12",
            'content': [
                {
                    'title': '',
                    'kind': 'table',
                    'data': table,
                    'header': 'row',
                    'style': 'hidden'
                },
                {
                    'title': '',
                    'kind': 'table',
                    'data': [['Total Time', humanize_duration(session.total_time())],
                             ['First Login', session.stretches.last() and timezone.datetime.strftime(session.start(), '%c') or ''],
                             ['Datasets', data.filter(kind="MX_DATA").count()],
                             ['Screens', data.filter(kind="MX_SCREEN").count()]],
                    'header': 'column',
                    'style': 'col-xs-6',
                },
                {
                    'title': '',
                    'kind': 'table',
                    'data': [['Shutter Open', humanize_duration(hours=sum([d.exposure_time * d.num_frames() for d in data.all()]) / 3600., sec=True)],
                             ['Last Dataset', data.last() and timezone.datetime.strftime(data.last().created, '%c') or ''],
                             ['Avg Frames/Dataset', sum([len(d.frames) for d in data.filter(kind="MX_DATA")]) / data.filter(
                                  kind="MX_DATA").count() if data.filter(kind="MX_DATA").count() else 0],
                             ['Avg Frames/Screen', sum([len(d.frames) for d in data.filter(kind="MX_SCREEN")]) / data.filter(
                                  kind="MX_SCREEN").count() if data.filter(kind="MX_SCREEN").count() else 0]],
                    'header': 'column',
                    'style': 'col-xs-6',
                },
            ]
        }
    ]}
    return mark_safe(json.dumps(stats))


@register.assignment_tag(takes_context=False)
def get_session_gaps(data):
    data = data.order_by('created')
    gaps = []
    for i in range(data.count()-1):
        if data[i].created <= (started(data[i+1]) - timedelta(minutes=10)):
            gaps.append([data[i].created, started(data[i+1]), humanize_duration((started(data[i+1])-data[i].created).total_seconds()/3600.)])
    return gaps


@register.filter
def started(data):
    return data.created - timedelta(seconds=(data.exposure_time*data.num_frames()))


def summarize_activity(qset):
    types = [k for k, _ in Data.DATA_TYPES]
    stats = {k: {'total': 0, 'year': defaultdict(int)} for k in types}

    for p in qset.all():
        yr = p.created.year
        k = p.kind
        stats[k]['total'] += 1
        stats[k]['year'][yr] += 1

    yrs = sorted({v['created'].year for v in Data.objects.values("created").order_by("created").distinct()})
    cols = [''] + yrs + ['All']
    _tbl = [cols]
    for k in types:
        r = [stats[k]['year'][yr] for yr in yrs]
        if sum(r) > 0:
            r = [Data.DATA_TYPES[k]] + r + [sum(r)]
            _tbl.append(r)
    r = ['Total'] + [sum(xr[1:]) for xr in zip(*_tbl)[1:]]
    rem_col = []
    for i, v in enumerate(r):
        if v == 'Total': continue
        if v > 0:
            break
        else:
            rem_col.append(i)

    _tbl.append(r)
    return _tbl