import calendar
from collections import defaultdict
from datetime import datetime
from math import ceil

import numpy
from django.conf import settings
from django.db.models import Count, Sum, F, Avg, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.timesince import timesince
from memoize import memoize

from mxlive.lims.models import Data, Sample, Session, Project, AnalysisReport, Container, Shipment, ProjectType, SupportArea, UserFeedback, UserAreaFeedback
from mxlive.utils.functions import ShiftEnd, ShiftStart, ShiftIndex
from mxlive.utils.misc import humanize_duration, natural_duration

HOUR_SECONDS = 3600
SHIFT = getattr(settings, "HOURS_PER_SHIFT", 8)
SHIFT_SECONDS = SHIFT * HOUR_SECONDS
MAX_COLUMN_USERS = 30


class ColorScheme(object):
    Live4 = ["#8f9f9a", "#c56052", "#9f6dbf", "#a0b552"]
    Live8 = ["#073B4C", "#06D6A0", "#FFD166", "#EF476F", "#118AB2", "#7F7EFF", "#afc765", "#78C5E7"]
    Live16 = [
        "#67aec1", "#c45a81", "#cdc339", "#ae8e6b", "#6dc758", "#a084b6", "#667ccd", "#cd4f55",
        "#805cd6", "#cf622d", "#a69e4c", "#9b9795", "#6db586", "#c255b6", "#073B4C", "#FFD166",
    ]


def js_epoch(dt):
    return int("{:0.0f}000".format(dt.timestamp() if dt else datetime.now().timestamp()))


@memoize(timeout=HOUR_SECONDS)
def get_data_periods(period='year'):
    field = 'created__{}'.format(period)
    return sorted(Data.objects.values_list(field, flat=True).distinct())


def usage_stats(beamline, period='year', **filters):
    periods = get_data_periods(period=period)
    field = 'created__{}'.format(period)
    sample_counts = {
        entry[field]: entry['count']
        for entry in
        Sample.objects.filter(datasets__beamline=beamline, **filters).values(field).order_by(field).annotate(
            count=Count('id'))
    }

    project_info = Session.objects.filter(beamline=beamline, **filters).values(field,
                                                                               'project__name').distinct().order_by(
        field, 'project__name').annotate(count=Count('project__name'))
    project_counts = defaultdict(int)
    project_names = defaultdict(list)
    for info in project_info:
        project_counts[info[field]] += 1
        project_names[info[field]].append(info['project__name'])

    new_project_info = Project.objects.filter(sessions__beamline=beamline, **filters).values(field, 'name').order_by(
        field, 'name').annotate(count=Count('name'))
    new_project_counts = defaultdict(int)
    new_project_names = defaultdict(list)
    for info in new_project_info:
        if info['count'] > 0:
            new_project_counts[info[field]] += 1
            new_project_names[info[field]].append(info['name'])

    session_counts_info = beamline.sessions.filter(**filters).values(field).order_by(field).annotate(count=Count('id'))
    session_params = beamline.sessions.filter(**filters).values(field).order_by(field).annotate(
        duration=Sum(
            Coalesce('stretches__end', timezone.now()) - F('stretches__start'),
        ),
        shift_duration=Sum(
            ShiftEnd(Coalesce('stretches__end', timezone.now())) - ShiftStart('stretches__start')
        ),
    )

    session_counts = {
        entry[field]: entry['count']
        for entry in session_counts_info
    }
    session_shifts = {
        entry[field]: ceil(entry['shift_duration'].total_seconds() / SHIFT_SECONDS)
        for entry in session_params
    }
    session_hours = {
        entry[field]: entry['duration'].total_seconds() / HOUR_SECONDS
        for entry in session_params
    }

    session_efficiency = {
        key: session_hours.get(key, 0) / (SHIFT * session_shifts.get(key, 1))
        for key in periods
    }

    data_params = beamline.datasets.filter(**filters).values(field).order_by(field).annotate(
        count=Count('id'), exposure=Avg('exposure_time'),
        duration=Sum(F('end_time') - F('start_time'))
    )

    shift_params = beamline.datasets.filter(**filters).annotate(shift=ShiftIndex('end_time')).values(
        'shift', 'end_time__week_day').order_by('end_time__week_day', 'shift').annotate(count=Count('id'))

    day_shift_counts = defaultdict(dict)
    day_names = list(calendar.day_abbr)
    for entry in shift_params:
        day = calendar.day_abbr[(entry['end_time__week_day'] - 2) % 7]
        day_part = '{:02d}:00 Shift'.format(entry['shift'] * SHIFT)
        day_shift_counts[day][day_part] = entry['count']
        day_shift_counts[day]['Day'] = day

    category_params = beamline.datasets.filter(**filters).values('project__kind__name').order_by(
        'project__kind__name').annotate(count=Count('id'))
    category_counts = {
        entry['project__kind__name']: entry['count']
        for entry in category_params
    }

    dataset_counts = {
        entry[field]: entry['count']
        for entry in data_params
    }
    dataset_exposure = {
        entry[field]: round(entry['exposure'], 3)
        for entry in data_params
    }

    dataset_durations = {
        entry[field]: entry['duration'].total_seconds() / HOUR_SECONDS
        for entry in data_params
    }

    dataset_efficiency = {
        key: dataset_durations.get(key, 0) / (session_hours.get(key, 1))
        for key in periods
    }

    dataset_per_shift = {
        key: dataset_counts.get(key, 0) / session_shifts.get(key, 1)
        for key in periods
    }

    dataset_per_hour = {
        key: dataset_counts.get(key, 0) / dataset_durations.get(key, 1)
        for key in periods
    }

    minutes_per_dataset = {
        key: dataset_durations.get(key, 0) * 60 / dataset_counts.get(key, 1)
        for key in periods
    }

    samples_per_dataset = {
        key: sample_counts.get(key, 0) / dataset_counts.get(key, 1)
        for key in periods
    }

    # Dataset statistics
    data_types = beamline.datasets.filter(**filters).values('kind__name').order_by('kind__name').annotate(
        count=Count('id'))

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

    # user statistics
    user_data_info = beamline.datasets.filter(**filters).values(user=F('project__name')).order_by('user').annotate(
        count=Count('id'),
        shutters=Sum(F('end_time') - F('start_time'))
    )
    user_session_info = beamline.sessions.filter(**filters).values(user=F('project__name'),
                                                                   kind=F('project__kind__name')).order_by(
        'user').annotate(
        duration=Sum(
            Coalesce('stretches__end', timezone.now()) - F('stretches__start'),
        ),
        shift_duration=Sum(
            ShiftEnd(Coalesce('stretches__end', timezone.now())) - ShiftStart('stretches__start')
        ),
    )

    user_sample_info = Sample.objects.filter(
        datasets__beamline=beamline, **filters
    ).values(user=F('project__name')).order_by('user').annotate(
        count=Count('id'),
    )

    project_type_colors = {
        kind: ColorScheme.Live8[i]
        for i, kind in enumerate(ProjectType.objects.values_list('name', flat=True).order_by('-name'))
    }

    user_datasets = {
        info['user']: info["count"]
        for info in user_data_info
    }

    user_types = {
        info['user']: info["kind"]
        for info in user_session_info
    }
    user_shift_duration = {
        info['user']: info["shift_duration"].total_seconds() / HOUR_SECONDS
        for info in user_session_info
    }
    user_samples = {
        info['user']: info["count"]
        for info in user_sample_info
    }
    user_duration = {
        info['user']: info["duration"].total_seconds() / HOUR_SECONDS
        for info in user_session_info
    }
    user_shutters = {
        info['user']: info["shutters"].total_seconds() / HOUR_SECONDS
        for info in user_data_info
    }

    user_efficiency = {
        user: min(100, 100*user_shutters.get(user, 0) / (hours or 1))
        for user, hours in user_duration.items()
    }

    user_schedule_efficiency = {
        user: min(100, 100*user_duration.get(user, 0) / (hours or 1))
        for user, hours in user_shift_duration.items()
    }

    beamtime = {}
    if settings.LIMS_USE_SCHEDULE:
        from mxlive.schedule.stats import beamtime_stats

        beamtime = beamtime_stats(beamline, period, **filters)

    stats = {'details': [
        {
            'title': 'Metrics Overview',
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
                    'kind': 'columnchart',
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
                            'y1': [['Datasets/Shift'] + [round(dataset_per_shift.get(per, 0), 2) for per in periods]],
                            'y2': [['Average Exposure'] + [round(dataset_exposure.get(per, 0), 2) for per in periods]],
                            'x-scale': x_scale,
                            'time-format': time_format
                        },
                    'style': 'col-12 col-md-6',
                },
                {
                    'title': 'Datasets by time of week',
                    'kind': 'columnchart',
                    'data': {
                        'x-label': 'Day',
                        'data': [
                            dict(day_shift_counts[day]) for day in day_names
                        ]
                    },
                    'style': 'col-12 col-md-6'
                },
                {
                    'title': 'Datasets by Project Type',
                    'kind': 'pie',
                    'data': {
                        'data': [
                            {'label': key or 'Unknown', 'value': count} for key, count in category_counts.items()
                        ],
                    },
                    'style': 'col-12 col-md-6'
                },
            ]
        },
        {
            'title': 'Data Summary',
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
                    'kind': 'columnchart',
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
                    'data': {
                        "colors": "Live16",
                        "data": [
                            {'label': entry['kind__name'] or 'Unknown', 'value': entry['count']} for entry in data_types
                        ],
                    },
                    'style': 'col-12 col-md-6'
                }
            ]
        },
        beamtime,
        {
            'title': 'User Statistics',
            'style': "row",
            'content': [
                {
                    'title': 'Datasets',
                    'kind': 'barchart',
                    'data': {
                        'x-label': 'User',
                        'aspect-ratio': .7,
                        'color-by': 'Type',
                        'colors': project_type_colors,
                        'data': [
                            {'User': user, 'Datasets': count, 'Type': user_types.get(user, 'Unknown')}
                            for user, count in sorted(user_datasets.items(), key=lambda v: v[1], reverse=True)[:MAX_COLUMN_USERS]
                        ],
                    },
                    'notes': (
                        "Dataset counts include all types of datasets. "
                        "Only the top {} users by number of datasets are shown"
                    ).format(MAX_COLUMN_USERS),
                    'style': 'col-12 col-md-4'
                },
                {
                    'title': 'Samples',
                    'kind': 'barchart',
                    'data': {
                        'x-label': 'User',
                        'aspect-ratio': .7,
                        'color-by': 'Type',
                        'colors': project_type_colors,
                        'data': [
                            {'User': user, 'Samples': count, 'Type': user_types.get(user, 'Unknown')}
                            for user, count in
                            sorted(user_samples.items(), key=lambda v: v[1], reverse=True)[:MAX_COLUMN_USERS]
                        ],
                    },
                    'notes': (
                        "Sample counts include only samples measured on the beamline. "
                        "Only the top {} users sample count shown"
                    ).format(MAX_COLUMN_USERS),
                    'style': 'col-12 col-md-4'
                },
                {
                    'title': 'Time Used',
                    'kind': 'barchart',
                    'data': {
                        'x-label': 'User',
                        'aspect-ratio': .7,
                        'color-by': 'Type',
                        'colors': project_type_colors,
                        'data': [
                            {'User': user, 'Hours': round(hours, 1), 'Type': user_types.get(user, 'Unknown')}
                            for user, hours in sorted(user_duration.items(), key=lambda v: v[1], reverse=True)[:MAX_COLUMN_USERS]
                        ],
                    },
                    "notes": (
                        "Total time is sum of active session durations for each user. Only the top {} "
                        "users are shown."
                    ).format(MAX_COLUMN_USERS),
                    'style': 'col-12 col-md-4'
                },
                {
                    'title': 'Efficiency',
                    'kind': 'barchart',
                    'data': {
                        'x-label': 'User',
                        'aspect-ratio': .7,
                        'color-by': 'Type',
                        'colors': project_type_colors,
                        'data': [
                            {'User': user, 'Percent': round(percent, 1), 'Type': user_types.get(user, 'Unknown')}
                            for user, percent in
                            sorted(user_efficiency.items(), key=lambda v: v[1], reverse=True)[:MAX_COLUMN_USERS]
                        ],
                    },
                    "notes": (
                        "Efficiency is the percentage of Time Used during which shutters were open. This measures how "
                        "effectively users are using their active session for data collection. "
                        "Only the top {} users are shown."
                    ).format(MAX_COLUMN_USERS),
                    'style': 'col-12 col-md-4'
                },
                {
                    'title': 'Schedule Efficiency',
                    'kind': 'barchart',
                    'data': {
                        'x-label': 'User',
                        'aspect-ratio': .7,
                        'color-by': 'Type',
                        'colors': project_type_colors,
                        'data': [
                            {'User': user, 'Percent': round(percent, 1), 'Type': user_types.get(user, 'Unknown')}
                            for user, percent in
                            sorted(user_schedule_efficiency.items(), key=lambda v: v[1], reverse=True)[:MAX_COLUMN_USERS]
                        ],
                    },
                    "notes": (
                        "Schedule Efficiency is the percentage of shift time during which a session "
                        "was active. This measures how effectively users are using full scheduled shifts for "
                        "data collection. Only the top {} users are shown."
                    ).format(MAX_COLUMN_USERS),
                    'style': 'col-12 col-md-4'
                },
            ],
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
    for field_name in ('score',)
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
    centers = (edges[:-1] + edges[1:]) * 0.5
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
        [float(d['score']) for d in report_info if d['score'] > -0.1],
        range=PARAMETER_RANGES.get('score')
    )
    return histograms


def parameter_stats(beamline, **filters):
    beam_sizes = Data.objects.filter(beamline=beamline, beam_size__isnull=False, **filters).values(
        'beam_size').order_by('beam_size').annotate(
        count=Count('id')
    )

    report_info = AnalysisReport.objects.filter(data__beamline=beamline, **filters).values('score')
    data_info = Data.objects.filter(beamline=beamline, **filters).values('exposure_time', 'attenuation', 'energy',
                                                                         'num_frames')
    param_histograms = make_parameter_histogram(data_info, report_info)

    stats = {'details': [
        {
            'title': 'Parameter Distributions',
            'style': 'row',
            'content': [
                           {
                               'title': 'Beam Size',
                               'kind': 'pie',
                               'data': {
                                   'data': [
                                       {'label': "{:0.0f}".format(entry['beam_size']), 'value': entry['count']}
                                       for entry in beam_sizes
                                   ]
                               },
                               'style': 'col-12 col-md-6'
                           },
                       ] + [
                           {
                               'title': PARAMETER_NAMES[param].title(),
                               'kind': 'histogram',
                               'data': {
                                   'data': [
                                       {"x": row[0], "y": row[1]} for row in param_histograms[param]
                                   ],
                               },
                               'style': 'col-12 col-md-6'
                           } for param in ('score', 'energy', 'exposure_time', 'attenuation', 'num_frames')
                       ]
        }
    ]}
    return stats


def session_stats(session):
    data_extras = session.datasets.values(key=F('kind__name')).order_by('key').annotate(
        count=Count('id'), time=Sum(F('exposure_time') * F('num_frames'), output_field=FloatField()),
        frames=Sum('num_frames'),
    )

    data_stats = [
        ['Avg Frames/{}'.format(info['key']), round(info['frames'] / info['count'], 1)]
        for info in data_extras
    ]
    data_counts = [
        [info['key'], round(info['count'], 1)]
        for info in data_extras
    ]

    data_info = session.datasets.values('exposure_time', 'attenuation', 'energy', 'num_frames')
    report_info = AnalysisReport.objects.filter(data__session=session).values('score')
    param_histograms = make_parameter_histogram(data_info, report_info)

    shutters = sum([info['time'] for info in data_extras]) / HOUR_SECONDS
    total_time = session.total_time()
    last_data = session.datasets.last()

    timeline_data = [
        {
            "type": data['kind__name'],
            "start": js_epoch(data['start_time']),
            "end": js_epoch(data['end_time']),
            "label": "{}: {}".format(data["kind__name"], data['name'])
        }
        for data in session.datasets.values('start_time', 'end_time', 'kind__name', 'name')
    ]
    stats = {'details': [
        {
            'title': 'Session Parameters',
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
                                               humanize_duration(shutters),
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
                               'kind': 'columnchart',
                               'data': {
                                   'x-label': 'Data Type',
                                   'data': [{
                                       'Data Type': row['key'],
                                       'Total': row['count'],
                                   }
                                       for row in data_extras
                                   ]
                               },
                               'style': 'col-12 col-md-6'
                           }

                       ] + [
                           {
                               'title': PARAMETER_NAMES[param].title(),
                               'kind': 'histogram',
                               'data': {
                                   'data': [
                                       {"x": row[0], "y": row[1]} for row in param_histograms[param]
                                   ],
                               },
                               'style': 'col-12 col-md-6'
                           } for param in ('score', 'energy', 'exposure_time', 'attenuation', 'num_frames')
                       ] + [

                       ]
        },
        {
            'title': 'Session Timeline',
            'description': (
                'Timeline of data collection for various types of '
                'datasets during the whole session from {} to {}'
            ).format(session.start().strftime('%c'), session.end().strftime('%c')),
            'style': "row",
            'content': [
                {
                    'title': 'Session Timeline',
                    'kind': 'timeline',
                    'start': js_epoch(session.start()),
                    'end': js_epoch(session.end()),
                    'data': timeline_data,
                    'style': 'col-12'
                },
                {
                    'title': 'Inactivity Gaps',
                    'kind': 'table',
                    'data': [
                                ['', 'Start', 'End', 'Duration']] + [
                                [i + 1, gap[0].strftime('%c'), gap[1].strftime('%c'), natural_duration(gap[2])]
                                for i, gap in enumerate(session.gaps())
                            ],
                    'header': 'row',
                    'notes': "Periods of possible inactivity while the session was open, greater than 10 minutes",
                    'style': 'col-12',
                },

            ]

        }

    ]}
    return stats


def project_stats(project, **filters):
    period = 'year'
    periods = get_data_periods()
    field = 'created__{}'.format(period)

    session_counts_info = project.sessions.filter(**filters).values(field).order_by(field).annotate(count=Count('id'))
    session_params = project.sessions.filter(**filters).values(field).order_by(field).annotate(
        shift_duration=Sum(
            ShiftEnd(Coalesce('stretches__end', timezone.now())) - ShiftStart('stretches__start')
        ),
        duration=Sum(
            Coalesce('stretches__end', timezone.now()) - F('stretches__start'),
        ),
    )

    session_counts = {
        entry[field]: entry['count']
        for entry in session_counts_info
    }
    session_shifts = {
        entry[field]: ceil(entry['shift_duration'].total_seconds() / SHIFT_SECONDS)
        for entry in session_params
    }
    session_hours = {
        entry[field]: entry['duration'].total_seconds() / HOUR_SECONDS
        for entry in session_params
    }

    session_efficiency = {
        key: session_hours.get(key, 0) / (SHIFT * session_shifts.get(key, 1))
        for key in periods
    }

    data_params = project.datasets.filter(**filters).values(field).order_by(field).annotate(
        count=Count('id'), exposure=Avg('exposure_time'),
        duration=Sum(F('end_time') - F('start_time'))
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
        entry[field]: entry['duration'].total_seconds() / HOUR_SECONDS
        for entry in data_params
    }

    dataset_per_shift = {
        key: dataset_counts.get(key, 0) / session_shifts.get(key, 1)
        for key in periods
    }

    dataset_per_hour = {
        key: dataset_counts.get(key, 0) / dataset_durations.get(key, 1)
        for key in periods
    }

    minutes_per_dataset = {
        key: dataset_durations.get(key, 0) * 60 / dataset_counts.get(key, 1)
        for key in periods
    }
    sample_counts = {
        entry[field]: entry['count']
        for entry in
        project.samples.filter(**filters).values(field).order_by(field).annotate(count=Count('id'))
    }
    samples_per_dataset = {
        key: sample_counts.get(key, 0) / dataset_counts.get(key, 1)
        for key in periods
    }

    data_types = project.datasets.filter(**filters).values('kind__name').order_by('kind__name').annotate(
        count=Count('id'))

    shift_params = project.datasets.filter(**filters).annotate(shift=ShiftIndex('end_time')).values(
        'shift', 'end_time__week_day').order_by('end_time__week_day', 'shift').annotate(count=Count('id'))

    day_shift_counts = defaultdict(dict)
    day_names = list(calendar.day_abbr)
    for entry in shift_params:
        day = calendar.day_abbr[(entry['end_time__week_day'] - 2) % 7]
        day_part = '{:02d}:00 Shift'.format(entry['shift'] * SHIFT)
        day_shift_counts[day][day_part] = entry['count']
        day_shift_counts[day]['Day'] = day

    shifts = sum(session_shifts.values())
    ttime = sum(session_hours.values())
    shutters = sum(dataset_durations.values())

    period_data = defaultdict(lambda: defaultdict(int))
    for summary in project.datasets.filter(**filters).values(field, 'kind__name').annotate(count=Count('pk')):
        period_data[summary[field]][summary['kind__name']] = summary['count']
    datatype_table = []
    for item in data_types:
        kind_counts = [period_data[per][item['kind__name']] for per in periods]
        datatype_table.append([item['kind__name']] + kind_counts + [sum(kind_counts)])
    period_counts = [sum(period_data[per].values()) for per in periods]
    datatype_table.append(['Total'] + period_counts + [sum(period_counts)])
    chart_data = []

    period_names = periods
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
        series = {'Year': period_names[i]}
        series.update(period_data[per])
        chart_data.append(series)

    last_session = project.sessions.last()
    first_session = project.sessions.first()
    actual_time = 0 if not shifts else ttime / (shifts * SHIFT)
    first_session_time = "Never" if not first_session else '{} ago'.format(timesince(first_session.created))
    last_session_time = "Never" if not first_session else '{} ago'.format(timesince(last_session.created))

    sessions_total = ['Sessions', sum(session_counts.values())]
    shifts_used_total = ['Shifts Used', '{} ({})'.format(shifts, humanize_duration(shifts * SHIFT))]

    beamtime = []
    visits = []
    stat_table = []
    if settings.LIMS_USE_SCHEDULE:
        from mxlive.schedule.stats import beamtime_stats

        sched_field = field.replace('created', 'start')
        beamtime_counts = {
            e[sched_field]: e['count']
            for e in project.beamtime.filter(**filters, cancelled=False).values(sched_field).annotate(count=Count('id'))
        }
        beamtime_shifts = {
            e[sched_field]: ceil(e['shift_duration'].total_seconds() / SHIFT_SECONDS)
            for e in project.beamtime.filter(**filters, cancelled=False).with_duration().values(sched_field, 'shift_duration').order_by(sched_field)
        }
        visits = ['Visits Scheduled'] + [beamtime_counts.get(p, 0) for p in periods]
        beamtime = ['Shifts Scheduled'] + [beamtime_shifts.get(p, 0) for p in periods]
        scheduled_shifts = sum(beamtime_shifts.values())

        time_table = [
            ['Visits Scheduled', sum(beamtime_counts.values())],
            ['Shifts Scheduled', '{} ({})'.format(scheduled_shifts, humanize_duration(scheduled_shifts * SHIFT))],
            shifts_used_total
        ]
        stat_table = [sessions_total,]
    else:
        time_table = [
            shifts_used_total,
            sessions_total,
        ]

    stats = {'details': [
        {
            'title': 'Data Collection Summary',
            'style': "row",
            'content': [
                {
                    'title': 'Time Usage',
                    'kind': 'table',
                    'data': time_table + [
                        ['Actual Time', '{:0.0%} ({})'.format(actual_time, humanize_duration(ttime))],
                        ['Shutters Open', '{}'.format(humanize_duration(shutters))],
                    ],
                    'header': 'column',
                    'style': 'col-sm-6'
                },
                {
                    'title': 'Overall Statistics',
                    'kind': 'table',
                    'data': stat_table + [
                        ['First Session', last_session_time],
                        ['Last Session', first_session_time],
                        ['Shipments / Containers', "{} / {}".format(
                            project.shipments.count(),
                            project.containers.filter(status__gte=Container.STATES.ON_SITE).count()
                        )],
                        ['Groups / Samples', "{} / {}".format(
                            project.sample_groups.filter(shipment__status__gte=Shipment.STATES.ON_SITE).count(),
                            project.samples.filter(container__status__gte=Container.STATES.ON_SITE).count())],
                    ],
                    'header': 'column',
                    'style': 'col-sm-6'
                },
                {
                    'title': 'Usage Statistics',
                    'kind': 'table',
                    'data': [
                        ["Year"] + period_names,
                        ['Samples Measured'] + [sample_counts.get(p, 0) for p in periods],
                        ['Sessions'] + [session_counts.get(p, 0) for p in periods],
                        visits,
                        beamtime,
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
                    'kind': 'columnchart',
                    'data': {
                        'x-label': period.title(),
                        'colors': 'Live8',
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
                            'y1': [['Datasets/Shift'] + [round(dataset_per_shift.get(per, 0), 2) for per in periods]],
                            'y2': [['Average Exposure'] + [round(dataset_exposure.get(per, 0), 2) for per in periods]],
                            'x-scale': x_scale,
                            'time-format': time_format
                        },
                    'style': 'col-12 col-md-6',
                },
            ]
        }
    ]}
    return stats


def support_stats():
    area_feedback = UserAreaFeedback.objects.all()
    choices = list(UserAreaFeedback.RATINGS)[:-1]
    choices = [choices[1], choices[0]] + choices[2:]
    colors = ['#66ffd5', '#00E6E2', '#ffdd33', '#ffa333']
    choice_colors = dict(zip([c[1] for c in choices], colors))

    likert_data = [
        {
            'Area': area.name,
            'data': {
                c[1]: area_feedback.filter(area=area, rating=c[0]).count() * (c[0] < 0 and -1 or 1)
            for c in choices }
         } for area in SupportArea.objects.filter(user_feedback=True)
    ]
    for i, d in enumerate(likert_data):
        likert_data[i].update(d['data'])
        likert_data[i].pop('data')

    stats = {'details': [
        {
            'title': 'User Experience Surveys',
            'description': 'Summary of impressions from user experience surveys',
            'style': "row",
            'content': [
                           {
                               'title': 'Ratings',
                               'kind': 'barchart',
                               'data': {
                                   'stack': [[c[1] for c in choices]],
                                   'x-label': 'Area',
                                   'aspect-ratio': 1.25,
                                   'colors': choice_colors,
                                   'data': likert_data,
                               },
                               'style': 'col-12'
                           },
                       ]
        },
    ]}
    return stats

