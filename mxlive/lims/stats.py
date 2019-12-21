import calendar
from collections import defaultdict
from datetime import datetime
from math import ceil

from django.conf import settings
from django.db.models import Count, Sum, Q, F, Avg, FloatField
from django.utils import timezone
from memoize import memoize

from mxlive.lims.models import Data, Sample, Session, DataType, Project
from mxlive.utils.functions import ShiftEnd, ShiftStart

SHIFT = getattr(settings, "SHIFT_LENGTH", 8)
SHIFT_SECONDS = SHIFT*3600


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
            ShiftEnd('stretches__end') - ShiftStart('stretches__start'), filter=Q(stretches__end__isnull=False)
        )
    )

    session_used_durations = Session.objects.filter(beamline=beamline, **filters).values(field).order_by(field).annotate(
        duration=Sum(
            F('stretches__end') - F('stretches__start'), filter=Q(stretches__end__isnull=False)
        )
    )

    session_counts = {
        entry[field]: entry['count']
        for entry in session_params
    }
    session_shifts = {
        entry[field]: ceil(entry['duration'].total_seconds()/(SHIFT_SECONDS))
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
        duration=Sum(F('exposure_time')*F('num_frames'), output_field=FloatField())
    )

    dataset_counts = {
        entry[field]: entry['count']
        for entry in data_params
    }
    dataset_exposure = {
        entry[field]: entry['exposure']
        for entry in data_params
    }

    dataset_durations = {
        entry[field]: entry['duration']/3600
        for entry in data_params
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
    data_types = list(
        DataType.objects.annotate(count=Count('datasets', filter=Q(datasets__beamline=beamline))).filter(count__gt=0))
    period_data = defaultdict(lambda: defaultdict(int))
    for summary in beamline.datasets.filter(**filters).values(field, 'kind__name').annotate(count=Count('pk')):
        period_data[summary[field]][summary['kind__name']] = summary['count']
    datatype_table = []
    for key in data_types:
        kind_counts = [period_data[per][key.name] for per in periods]
        datatype_table.append([key.name] + kind_counts + [sum(kind_counts)])
    period_counts = [sum(period_data[per].values()) for per in periods]
    datatype_table.append(['Total'] + period_counts + [sum(period_counts)])
    histogram_data = []

    period_names = periods
    period_xvalues = periods
    x_scale = 'linear'
    time_format = ''

    if period == 'month':
        yr = timezone.now().year
        period_names = [calendar.month_abbr[per].title() for per in periods]
        period_xvalues = [datetime.strftime(datetime(yr, per, 1, 0, 0), '%c') for per in periods]
        time_format = '%m'
        x_scale = 'time'
    elif period == 'year':
        period_xvalues = [datetime.strftime(datetime(per, 1, 1, 0, 0), '%c') for per in periods]
        time_format = '%Y'
        x_scale = 'time'

    # data histogram
    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(period_data[per])
        histogram_data.append(series)

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
                    'kind': 'histogram',
                    'data': {
                        'x-label': period.title(),
                        'data': [
                            {
                                period.title(): period_names[i],
                                'Samples': sample_counts.get(per, 0),
                                'Datasets': dataset_counts.get(per, 0),
                                'Total Time': session_hours.get(per,0),
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
                            'y1': [['Datasets/Shift'] + list(dataset_per_shift.values())],
                            'y2': [['Average Exposure Time'] + list(dataset_exposure.values())],
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
                    'kind': 'histogram',
                    'data': {
                        'x-label': period.title(),
                        'data': histogram_data,
                    },
                    'style': 'col-12 col-sm-6'
                }
            ]
        },
    ]
    }
    return stats