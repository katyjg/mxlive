import calendar
from collections import defaultdict
from datetime import datetime
from math import ceil

import numpy

from django.conf import settings
from django.db.models import Count, Sum, Q, F, Avg, FloatField, Max
from django.db.models.functions import Coalesce
from django.utils import timezone
from memoize import memoize

from mxlive.lims.models import Data, Sample, Session, DataType, Project, AnalysisReport
from mxlive.utils.functions import ShiftEnd, ShiftStart
from mxlive.utils.misc import humanize_duration

SHIFT = getattr(settings, "SHIFT_LENGTH", 8)
SHIFT_SECONDS = SHIFT*3600


def js_epoch(dt):
    return int("{:0.0f}000".format(dt.timestamp() if dt else datetime.now().timestamp()))


@memoize(timeout=3600)
def get_data_periods(period='year'):
    field = 'created__{}'.format(period)
    return sorted(Data.objects.values_list(field, flat=True).distinct())


def usage_stats(beamline, period='year', **filters):
    periods = get_data_periods(period=period)
    field = 'created__{}'.format(period)
    sample_counts = {
        entry[field]: entry['count']
        for entry in Sample.objects.filter(datasets__beamline=beamline, **filters).values(field).order_by(field).annotate(count=Count('id'))
    }

    project_info = Session.objects.filter(beamline=beamline, **filters).values(field, 'project__name').distinct().order_by(field, 'project__name').annotate(count=Count('project__name'))
    project_counts = defaultdict(int)
    project_names = defaultdict(list)
    for info in project_info:
        project_counts[info[field]] += 1
        project_names[info[field]].append(info['project__name'])

    new_project_info = Project.objects.filter(sessions__beamline=beamline, **filters).values(field, 'name').order_by(field, 'name').annotate(count=Count('name'))
    new_project_counts = defaultdict(int)
    new_project_names = defaultdict(list)
    for info in new_project_info:
        if info['count'] > 0:
            new_project_counts[info[field]] += 1
            new_project_names[info[field]].append(info['name'])

    session_params = beamline.sessions.filter(**filters).values(field).order_by(field).annotate(count=Count('id'))
    session_shift_durations = Session.objects.filter(beamline=beamline, **filters).values(field).order_by(field).annotate(
        duration=Sum(
            ShiftEnd(Coalesce('stretches__end', timezone.now())) - ShiftStart('stretches__start')
        )
    )

    session_used_durations = Session.objects.filter(beamline=beamline, **filters).values(field).order_by(field).annotate(
        duration=Sum(
            Coalesce('stretches__end', timezone.now()) - F('stretches__start'),
        )
    )

    session_counts = {
        entry[field]: entry['count']
        for entry in session_params
    }
    session_shifts = {
        entry[field]: ceil(entry['duration'].total_seconds()/SHIFT_SECONDS)
        for entry in session_shift_durations
    }
    session_hours = {
        entry[field]: entry['duration'].total_seconds()/3600
        for entry in session_used_durations
    }

    session_efficiency = {
        key: session_hours.get(key, 0)/(SHIFT*session_shifts.get(key, 1))
        for key in periods
    }

    data_params = beamline.datasets.filter(**filters).values(field).order_by(field).annotate(
        count=Count('id'), exposure=Avg('exposure_time'),
        duration=Sum(F('end_time')-F('start_time'))
    )

    dataset_counts = {
        entry[field]: entry['count']
        for entry in data_params
    }
    dataset_exposure = {
        entry[field]: round(entry['exposure'], 3)
        for entry in data_params
    }

    dataset_durations = {
        entry[field]: entry['duration'].total_seconds()/3600
        for entry in data_params
    }

    dataset_efficiency = {
        key: dataset_durations.get(key, 0) / (session_hours.get(key, 1))
        for key in periods
    }

    dataset_per_shift = {
        key: dataset_counts.get(key, 0)/session_shifts.get(key, 1)
        for key in periods
    }

    dataset_per_hour = {
        key: dataset_counts.get(key, 0)/dataset_durations.get(key, 1)
        for key in periods
    }

    minutes_per_dataset = {
        key: dataset_durations.get(key, 0)*60/dataset_counts.get(key, 1)
        for key in periods
    }

    samples_per_dataset = {
        key: sample_counts.get(key, 0)/dataset_counts.get(key, 1)
        for key in periods
    }

    # Dataset statistics
    data_types = beamline.datasets.filter(**filters).values('kind__name').order_by('kind__name').annotate(count=Count('id'))

    period_data = defaultdict(lambda: defaultdict(int))
    for summary in beamline.datasets.filter(**filters).values(field, 'kind__name').annotate(count=Count('pk')):
        period_data[summary[field]][summary['kind__name']] = summary['count']
    datatype_table = []
    for item in data_types:
        kind_counts = [period_data[per][item['kind__name']] for per in periods]
        datatype_table.append([item['kind__name']] + kind_counts + [sum(kind_counts)])
    period_counts = [sum(period_data[per].values()) for per in periods]
    datatype_table.append(['Total'] + period_counts + [sum(period_counts)])
    chart_data = []

    period_names = periods
    period_xvalues = periods
    x_scale = 'linear'
    time_format = ''

    if period == 'month':
        yr = timezone.now().year
        period_names = [calendar.month_abbr[per].title() for per in periods]
        period_xvalues = [datetime.strftime(datetime(yr, per, 1, 0, 0), '%c') for per in periods]
        time_format = '%b'
        x_scale = 'time'
    elif period == 'year':
        period_xvalues = [datetime.strftime(datetime(per, 1, 1, 0, 0), '%c') for per in periods]
        time_format = '%Y'
        x_scale = 'time'

    # data histogram
    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(period_data[per])
        chart_data.append(series)

    stats = {'details': [
        {
            'title': 'Usage Metrics',
            'style': 'row',
            'content': [
                {
                    'title': 'Usage Statistics',
                    'kind': 'table',
                    'data': [
                        [period.title()] + period_names,
                        ['Users'] + [project_counts.get(p, 0) for p in periods],
                        ['New Users'] + [new_project_counts.get(p, 0) for p in periods],
                        ['Samples Measured'] + [sample_counts.get(p, 0) for p in periods],
                        ['Sessions'] + [session_counts.get(p, 0) for p in periods],
                        ['Shifts Used'] + [session_shifts.get(p, 0) for p in periods],
                        ['Time Used¹ (hr)'] + ['{:0.1f}'.format(session_hours.get(p, 0)) for p in periods],
                        ['Usage Efficiency² (%)'] + ['{:.0%}'.format(session_efficiency.get(p, 0)) for p in periods],
                        ['Datasets³ Collected'] + [dataset_counts.get(p, 0) for p in periods],
                        ['Minutes/Dataset³'] + ['{:0.1f}'.format(minutes_per_dataset.get(p, 0)) for p in periods],
                        ['Datasets³/Hour'] + ['{:0.1f}'.format(dataset_per_hour.get(p, 0)) for p in periods],
                        ['Average Exposure (sec)'] + ['{:0.2f}'.format(dataset_exposure.get(p, 0)) for p in periods],
                        ['Samples/Dataset³'] + ['{:0.1f}'.format(samples_per_dataset.get(p, 0)) for p in periods],

                    ],
                    'style': 'col-12',
                    'header': 'column row',
                    'description': 'Summary of time, datasets and usage statistics',
                    'notes': (
                        ' 1. Time Used is the number of hours an active session was running on the beamline.  \n'
                        ' 2. Usage efficiency is the percentage of used shifts during which a session was active.  \n'
                        ' 3. All datasets are considered for this statistic irrespective of dataset type.'
                    )
                },
                {
                    'title': 'Usage Statistics',
                    'kind': 'barchart',
                    'data': {
                        'x-label': period.title(),
                        'data': [
                            {
                                period.title(): period_names[i],
                                'Samples': sample_counts.get(per, 0),
                                'Datasets': dataset_counts.get(per, 0),
                                'Total Time': round(session_hours.get(per, 0), 1),
                            } for i, per in enumerate(periods)
                        ]
                    },
                    'style': 'col-12 col-md-6'
                },
                {
                    'title': 'Productivity',
                    'kind': 'lineplot',
                    'data':
                        {
                            'x': [period.title()] + period_xvalues,
                            'y1': [['Datasets/Shift'] + [round(dataset_per_shift.get(per, 0),2) for per in periods]],
                            'y2': [['Average Exposure'] + [round(dataset_exposure.get(per, 0),2) for per in periods]],
                            'x-scale': x_scale,
                            'time-format': time_format
                        },
                    'style': 'col-12 col-md-6',
                }
            ]
        },
        {
            'title': 'Data Summary'.format(beamline.acronym),
            'style': "row",
            'content': [
                {
                    'title': 'Dataset summary by {}'.format(period),
                    'kind': 'table',
                    'data': [[''] + period_names + ['All']] + datatype_table,
                    'header': 'column row',
                    'style': 'col-12'
                },
                {
                    'title': 'Dataset summary by {}'.format(period),
                    'kind': 'barchart',
                    'data': {
                        'x-label': period.title(),
                        'stack': [[d['kind__name'] for d in data_types]],
                        'data': chart_data,
                    },
                    'style': 'col-12 col-md-6'
                },
                {
                    'title': 'Dataset Types',
                    'kind': 'pie',
                    'data': [
                        {
                            'label': entry['kind__name'],
                            'value': entry['count'],
                        }
                        for entry in data_types
                    ],
                    'style': 'col-12 col-md-6'
                },
            ]
        },
    ]
    }
    return stats


# Histogram Parameters
PARAMETER_NAMES = {
    field_name: Data._meta.get_field(field_name).verbose_name
    for field_name in ['exposure_time', 'attenuation', 'energy', 'num_frames']
}
PARAMETER_NAMES.update({
    field_name: AnalysisReport._meta.get_field(field_name).verbose_name
    for field_name in ('score', )
})

PARAMETER_RANGES = {
    'exposure_time': (0.01, 20),
    'score': (0.01, 1),
    'energy': (4., 18.)
}

PARAMETER_BINNING = {
    'energy': 8,
    'attenuation': numpy.linspace(0, 100, 11)
}


def get_histogram_points(data, range=None, bins='doane'):
    counts, edges = numpy.histogram(data, bins=bins, range=range)
    centers = (edges[:-1] + edges[1:])*0.5
    return list(zip(centers, counts))


def make_parameter_histogram(data_info, report_info):
    """
    Create a histogram for parameters in the query results
    :param data_info: Query result for data
    :param report_info: Query result for reports
    :return: histogram data
    """

    histograms = {
        field_name: get_histogram_points(
            [float(d[field_name]) for d in data_info if d[field_name] is not None],
            range=PARAMETER_RANGES.get(field_name), bins=PARAMETER_BINNING.get(field_name, 'doane')
        )
        for field_name in ('exposure_time', 'attenuation', 'energy', 'num_frames')
    }
    histograms['score'] = get_histogram_points(
        [float(d['score']) for d in report_info if d['score'] is not None],
        range=PARAMETER_RANGES.get('score')
    )
    return histograms


def parameter_stats(beamline, **filters):
    beam_sizes = Data.objects.filter(beamline=beamline, beam_size__isnull=False, **filters).values('beam_size').order_by('beam_size').annotate(
        count=Count('id')
    )

    report_info = AnalysisReport.objects.filter(data__beamline=beamline, **filters).values('score')
    data_info = Data.objects.filter(beamline=beamline, **filters).values('exposure_time', 'attenuation', 'energy', 'num_frames')
    param_histograms = make_parameter_histogram(data_info, report_info)

    stats = {'details': [
        {
            'title': 'Parameter Distributions',
            'style': 'row',
            'content': [
                {
                    'title': 'Beam Size',
                    'kind': 'pie',
                    'data': [
                        {
                            'label': "{:0.0f}".format(entry['beam_size']),
                            'value': entry['count'],
                        }
                        for entry in beam_sizes
                    ],
                    'style': 'col-12 col-md-6'
                },
            ] + [
                {
                    'title': PARAMETER_NAMES[param].title(),
                    'kind': 'histogram',
                    'data': [
                        {
                            "x": row[0],
                            "y": row[1]
                        }
                        for row in param_histograms[param]
                    ],
                    'style': 'col-12 col-md-6'
                } for param in ('score', 'energy', 'exposure_time', 'attenuation', 'num_frames')
            ]
        }
    ]}
    return stats


def session_stats(session):

    data_extras = session.datasets.values(key=F('kind__name')).order_by('key').annotate(
        count=Count('id'), time=Sum(F('exposure_time')*F('num_frames'), output_field=FloatField()),
        frames=Sum('num_frames'),
    )

    data_stats = [
        ['Avg Frames/{}'.format(info['key']), round(info['frames']/info['count'], 1)]
        for info in data_extras
    ]
    data_counts = [
        [info['key'], round(info['count'], 1)]
        for info in data_extras
    ]

    data_info = session.datasets.values('exposure_time', 'attenuation', 'energy', 'num_frames')
    report_info = AnalysisReport.objects.filter(data__session=session).values('score')
    param_histograms = make_parameter_histogram(data_info, report_info)

    shutters = sum([info['time'] for info in data_extras])/3600
    total_time = session.total_time()
    last_data = session.datasets.last()

    data_times = defaultdict(list)
    for data in session.datasets.values('start_time', 'end_time', 'kind__name'):
        data_times[data['kind__name']].append({
            'timeRange': [js_epoch(data['start_time']), js_epoch(data['end_time'])],
            'val': data['kind__name'],
        })

    timeline_info = [
        {
            "group": "Session",
            "data": [
                {
                    "label": key,
                    "data": data,
                } for key, data in data_times.items()
            ]
        }
    ]
    stats = {'details': [
        {
            'title': 'Session Statistics',
            'description': 'Data Collection Summary',
            'style': "row",
            'content': [
                {
                    'title': '',
                    'kind': 'table',
                    'data': [
                                ['Total Time', humanize_duration(total_time)],
                                ['First Login', timezone.localtime(session.start()).strftime('%c')],
                                ['Samples', session.samples().count()],
                            ] + data_counts,
                    'header': 'column',
                    'style': 'col-12 col-md-6',
                },
                {
                    'title': '',
                    'kind': 'table',
                    'data': [
                                ['Shutters Open', "{} ({:.2f}%)".format(
                                    humanize_duration(hours=shutters),
                                    shutters * 100 / total_time if total_time else 0)
                                ],
                                ['Last Dataset', '' if not last_data else last_data.modified.strftime('%c')],
                                ['No. of Logins', session.stretches.count()],
                            ] + data_stats,
                    'header': 'column',
                    'style': 'col-12 col-md-6',
                },
                {
                    'title': 'Types of data collected',
                    'kind': 'barchart',
                    'data': {
                        'x-label': 'Data Type',
                        'data': [{
                            'Data Type': row['key'],
                            'Total': row['count'],
                        }
                        for row in data_extras
                        ]
                    },
                    'style': 'col-12 col-md-4'
                }

            ] + [
                {
                    'title': PARAMETER_NAMES[param].title(),
                    'kind': 'histogram',
                    'data': [
                        {
                            "x": row[0],
                            "y": row[1]
                        }
                        for row in param_histograms[param]
                    ],
                    'style': 'col-12 col-md-4'
                } for param in ('score', 'energy', 'exposure_time', 'attenuation', 'num_frames')
            ] + [
                {
                    'title': 'Session Timeline',
                    'kind': 'timeline',
                    'data': timeline_info,
                    'style': 'col-12'
                }
            ]
        }
    ]}
    return stats