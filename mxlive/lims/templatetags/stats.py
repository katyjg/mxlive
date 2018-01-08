from django import template
from django.utils.safestring import mark_safe

from lims.models import *
from converter import humanize_duration

import json

register = template.Library()

COLOR_SCHEME = ["#883a6a", "#1f77b4", "#aec7e8", "#5cb85c", "#f0ad4e"]
SHIFT = getattr(settings, "SHIFT_LENGTH", 8)

@register.assignment_tag(takes_context=False)
def get_data_stats(bl, year):
    data = bl.data_set.all()
    years = sorted({v['created'].year for v in Data.objects.values("created").order_by("created").distinct()})
    kinds = [k for k in Data.DATA_TYPES if data.filter(kind=k[0]).exists()]
    yrs = [{'Year': yr} for yr in years]
    for yr in yrs:
        yr.update({k[1]: data.filter(created__year=yr['Year'], kind=k[0]).count() for k in kinds})
    yearly = [[k[1]] + [data.filter(created__year=yr, kind=k[0]).count() for yr in years] + [data.filter(kind=k[0]).count()] for k in kinds]
    totals = [['Total'] + [data.filter(created__year=yr).count() for yr in years] + [data.count()]]
    data = data.filter(created__year=year)
    stats = {'details': [
        {
            'title': '{} Summary'.format(bl.acronym),
            'description': 'Data Collection Summary for {}'.format(bl.name),
            'style': "col-xs-12",
            'content': [
                {
                    'title': '',
                    'kind': 'table',
                    'data': [[''] + years + ['All']] + yearly + totals,
                    'header': 'row',
                    'style': 'col-sm-8'
                },
                {
                    'title': '',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'Year',
                        'data': yrs,
                    },
                    'style': 'col-sm-4'
                }
            ]
        },
        {
            'title': '{} Beamline Parameters'.format(year),
            'description': 'Data Collection Parameters Summary',
            'style': 'col-xs-12',
            'content': [
                           {
                               'title': 'Attenuation vs. Exposure Time',
                               'kind': 'scatterplot',
                               'data':
                                   {'x': ['Exposure Time (s)'] + [d for d in
                                                                  data.values_list('exposure_time', flat=True)],
                                    'y1': [
                                        ['Attenuation (%)'] + [d for d in data.values_list('attenuation', flat=True)]],
                                    'x-scale': 'log'},
                               'style': 'col-xs-8'
                           } if data.count() else {},
                           {
                               'title': 'Beam Size',
                               'kind': 'pie',
                               'data': [
                                   {'label': "{}".format(d),
                                    'value': 360 * data.filter(beam_size=d).count() / data.count(),
                                    'color': COLOR_SCHEME[i]}
                                   for i, d in enumerate(data.values_list('beam_size', flat=True).distinct())
                                   ],
                               'style': 'col-xs-4'
                           } if data.count() else {},
                       ]
        },
        {
            'title': '',
            'style': 'col-xs-12',
            'content': [
                            {
                                'title': e.title(),
                                'kind': 'barchart',
                                'data': {
                                    'data': [float(d) for d in data.values_list(e, flat=True) if d != None],
                                    'color': [COLOR_SCHEME[i + 1]]
                                },
                                'style': 'col-xs-6 col-sm-4'
                            } for i, e in enumerate(['energy', 'exposure_time', 'attenuation'])] if data.count() else []
        }
    ]}
    return mark_safe(json.dumps(stats))

@register.assignment_tag(takes_context=False)
def get_usage_stats(bl, year):
    sessions = bl.sessions.filter(created__year=year).order_by('project')
    datasets = bl.data_set.filter(session__in=sessions)
    data = [
        [
            Project.objects.get(pk=p).username, # User
            sessions.filter(project=p).count(), # Sessions
            datasets.filter(kind='MX_DATA', project__pk=p).count(), # Full Datasets
            round(sum([d.total_angle() for d in datasets.filter(project__pk=p)])/360., 2), # Images
            total_shifts(sessions, p), # Shifts
            round(total_time(sessions, p), 2), # Total Time
            humanize_duration(total_time(sessions, p)), # Total Time
            int(total_time(sessions, p) / (total_shifts(sessions, p) * SHIFT) * 100), # Used Time (%)
            round(datasets.filter(kind='MX_DATA', project__pk=p).count() / total_time(sessions, p), 2) if total_time(sessions, p) else 0, # Datasets/Hour
        ]
        for p in sessions.values_list('project', flat=True).distinct()
    ]

    ttime = sum([u[5] for u in data])
    stats = {'details': [
        {
            'title': 'Usage Metrics',
            'style': 'col-xs-12',
            'content': [
                {
                    'title': 'Total Activity',
                    'kind': 'table',
                    'data': [['Shifts (or parts of shifts) Used', sum([u[4] for u in data])],
                             ['Datasets Collected', datasets.filter(kind='MX_DATA').count()],
                             ['Normalized Datasets', round(sum([u[3] for u in data]), 2)]],
                    'style': 'col-sm-6',
                    'header': 'column'
                },
                {
                    'title': 'Average Efficiency',
                    'kind': 'table',
                    'data': [['Actual Time Used (h)', "{} ({:.1f}%)".format(ttime, sum([u[4] for u in data])*8/ttime if ttime else 0)],
                             ['Datasets/Hour', round(datasets.filter(kind='MX_DATA').count() / ttime, 2) if ttime else 0],
                             ['Norm Data/Hour', round(sum([u[3] for u in data]) / ttime, 2) if ttime else 0]],
                    'style': 'col-sm-6',
                    'header': 'column'
                },
                {
                    'title': 'Time Used',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'User',
                        'data': [{'User': u[0], 'Efficiency': float(u[7]) / 100.} for u in sorted(data, key=lambda x: float(x[7]))],
                    },
                    'style': 'col-sm-12'
                },
                {
                    'title': 'Average Datasets* per Hour',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'User',
                        'data': [{'User': u[0], 'Normalized Datasets': u[3], 'Full Datasets': u[8]} for u in
                                 sorted(data, key=lambda x: float(x[3]))],
                    },
                    'style': 'col-sm-12'
                },
                {
                    'kind': 'table',
                    'description': "<td>*One normalized dataset is equivalent to 360 frames collected and uploaded</td>",
                    'header': 'row',
                    'data': [['User', 'Sessions', 'Full Datasets', 'Norm Datasets*', 'Shifts', 'Total Time', 'Used Time (%)', 'Datasets/Hour']] + [d[:5] + d[6:] for d in sorted(data, key=lambda x: x[7])]
                }
            ]
        }
    ]}
    return mark_safe(json.dumps(stats))


@register.assignment_tag(takes_context=False)
def get_session_stats(data, session):
    shutters = sum([d.exposure_time * d.num_frames() for d in data.all()]) / 3600.
    stats = {'details': [
        {
            'title': 'Beamline Control Statistics',
            'description': 'Data Collection Summary',
            'style': "col-xs-12",
            'content': [
                {
                    'title': '',
                    'kind': 'table',
                    'data': [['Total Time', humanize_duration(session.total_time())],
                             ['First Login', session.stretches.last() and datetime.strftime(timezone.localtime(session.start()), '%B %d, %Y %H:%M') or ''],
                             ['Datasets', data.filter(kind="MX_DATA").count()],
                             ['Screens', data.filter(kind="MX_SCREEN").count()]],
                    'header': 'column',
                    'style': 'col-xs-4',
                },
                {
                    'title': '',
                    'kind': 'table',
                    'data': [['Shutter Open', "{} ({:.2f}%)".format(humanize_duration(hours=shutters), shutters * 100 / session.total_time() if session.total_time() else 0 )],
                             ['Last Dataset', data.last() and datetime.strftime(timezone.localtime(data.last().modified), '%c') or ''],
                             ['Avg Frames/Dataset', sum([len(d.frames) for d in data.filter(kind="MX_DATA")]) / data.filter(
                                  kind="MX_DATA").count() if data.filter(kind="MX_DATA").count() else 0],
                             ['Avg Frames/Screen', sum([len(d.frames) for d in data.filter(kind="MX_SCREEN")]) / data.filter(
                                  kind="MX_SCREEN").count() if data.filter(kind="MX_SCREEN").count() else 0]],
                    'header': 'column',
                    'style': 'col-xs-4',
                },
                {
                    'title': '',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'Type',
                        'data': [{'Type': k, 'val': data.filter(kind=k).count()} for k in
                                 data.values_list('kind', flat=True).order_by('kind').distinct()],
                    },
                    'style': 'col-xs-4'
                }

            ]
        },
        {
            'title': 'Beamline Parameters',
            'description': 'Data Collection Parameters Summary',
            'style': 'col-xs-12',
            'content': [
                {
                    'title': 'Attenuation vs. Exposure Time',
                    'kind': 'scatterplot',
                    'data':
                        {'x': ['Exposure Time (s)'] + [d for d in data.values_list('exposure_time', flat=True)],
                         'y1': [['Attenuation (%)'] + [d for d in data.values_list('attenuation', flat=True)]]},
                    'style': 'col-xs-9'
                } if data.count() else {},
                {
                    'title': 'Beam Size',
                    'kind': 'pie',
                    'data': [
                        {'label': "{}".format(d),
                         'value': 360 * data.filter(beam_size=d).count() / data.count(),
                         'color': COLOR_SCHEME[i]}
                        for i, d in enumerate(data.values_list('beam_size', flat=True).distinct())
                        ],
                    'style': 'col-xs-3'
                } if data.count() else {},
            ] + [{
                'title': e.title(),
                'kind': 'histogram',
                'data': {
                    'x-label': e.title(),
                    'data': [{e.title(): str(v), 'val': data.filter(**{e: v}).count()}
                             for v in data.values_list(e, flat=True).order_by(e).distinct() if v != None],
                    'colors': [COLOR_SCHEME[i+1]]
                },
                'style': 'col-xs-4'
            } for i, e in enumerate(['energy', 'exposure_time', 'attenuation'])] if data.count() else []
        }
    ]}
    return mark_safe(json.dumps(stats))


@register.assignment_tag(takes_context=False)
def get_session_gaps(data):
    data = data.order_by('created')
    gaps = []
    for i in range(data.count()-1):
        if data[i].created <= (started(data[i+1]) - timedelta(minutes=10)):
            gaps.append([data[i].created, started(data[i+1]),
                         humanize_duration((started(data[i+1])-data[i].created).total_seconds()/3600.)])
    return gaps


@register.filter
def get_years(bl):
    return sorted({v['created'].year for v in Data.objects.filter(beamline=bl).values("created").order_by("created").distinct()})

@register.filter
def started(data):
    return data.modified - timedelta(seconds=(data.exposure_time*data.num_frames()))


def total_shifts(sessions, project):
    shifts = [y for x in [s.shifts() for s in sessions.filter(project=project)] for y in x]
    return len(set(shifts))


def total_time(sessions, project):
    return sum([s.total_time() for s in sessions.filter(project=project)])

