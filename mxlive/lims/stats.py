import calendar
from datetime import datetime
from math import ceil

from django.conf import settings
from django.db.models import Count, Sum, Q, F, Avg
from django.utils import timezone
from memoize import memoize

from mxlive.lims.models import Data, Sample, Session
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

    data_params = beamline.datasets.filter(kind__acronym__in=['DATA', 'XRD'], **filters).values(field).order_by(field).annotate(
        count=Count('id'), exposure=Avg('exposure_time')
    )
    dataset_counts = {
        entry[field]: entry['count']
        for entry in data_params
    }
    dataset_exposure = {
        entry[field]: entry['exposure']
        for entry in data_params
    }

    dataset_per_shift = {
        key: dataset_counts.get(key, 0)/session_shifts.get(key, 1)
        for key in periods
    }

    minutes_per_sample = {
        key: 60*session_hours.get(key, 0)/sample_counts.get(key, 1)
        for key in periods
    }

    samples_per_dataset = {
        key: sample_counts.get(key, 0)/dataset_counts.get(key, 1)
        for key in periods
    }

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
                        ['Samples Measured'] + [sample_counts.get(p, 0) for p in periods],
                        ['Sessions'] + [session_counts.get(p, 0) for p in periods],
                        ['Shifts Used'] + [session_shifts.get(p, 0) for p in periods],
                        ['Time Used (hr)'] + ['{:0.1f}'.format(session_hours.get(p, 0)) for p in periods],
                        ['Usage Efficiency (%)'] + ['{:.0%}'.format(session_efficiency.get(p, 0)) for p in periods],
                        ['Datasets Collected'] + [dataset_counts.get(p, 0) for p in periods],
                        ['Datasets/Shift'] + ['{:0.1f}'.format(dataset_per_shift.get(p, 0)) for p in periods],
                        ['Average Exposure Time (sec)'] + ['{:0.2f}'.format(dataset_exposure.get(p, 0)) for p in periods],
                        ['Time/Sample (min)'] + ['{:0.1f}'.format(minutes_per_sample.get(p, 0)) for p in periods],
                        ['Samples/Dataset'] + ['{:0.1f}'.format(samples_per_dataset.get(p, 0))  for p in periods],

                    ],
                    'style': 'col-12',
                    'header': 'column',
                    'notes': 'Total time is the number of hours an active session was running on the beamline.'
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
                    'notes': (
                        "Datasets/Shift is the average number of datasets collected per shift"
                        "used on the beamline."
                    )
                }
            ]
        }
    ]
    }
    return stats