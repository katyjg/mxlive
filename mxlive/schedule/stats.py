import calendar
from collections import defaultdict

from django.conf import settings
from django.db.models import Count, Sum

from memoize import memoize
from datetime import datetime

from mxlive.schedule.models import Beamtime, Downtime

HOUR_SECONDS = 3600
SHIFT = getattr(settings, "HOURS_PER_SHIFT", 8)


class ColorScheme(object):
    Live4 = ["#8f9f9a", "#c56052", "#9f6dbf", "#a0b552"]
    Live8 = ["#073B4C", "#06D6A0", "#FFD166", "#EF476F", "#118AB2", "#7F7EFF", "#afc765", "#78C5E7"]
    Live16 = [
        "#67aec1", "#c45a81", "#cdc339", "#ae8e6b", "#6dc758", "#a084b6", "#667ccd", "#cd4f55",
        "#805cd6", "#cf622d", "#a69e4c", "#9b9795", "#6db586", "#c255b6", "#073B4C", "#FFD166",
    ]


@memoize(timeout=HOUR_SECONDS)
def get_beamtime_periods(period='year', beamline=None):
    field = 'start__{}'.format(period)
    return sorted(Beamtime.objects.filter(beamline=beamline).values_list(field, flat=True).distinct())


def beamtime_stats(beamline, period='year', **filters):
    periods = get_beamtime_periods(period=period, beamline=beamline)
    filters = {k.replace('created', 'start'): v for k, v in filters.items()}
    field = 'start__{}'.format(period)

    beamtime_info = beamline.beamtime.with_duration().filter(**filters)

    start_yr = filters.get('start__{}'.format(period), beamtime_info.first().start.year)
    end_yr = filters and start_yr or datetime.now().year
    start = datetime(year=start_yr, month=1, day=1)
    end = min(datetime(year=end_yr, month=12, day=31), datetime.now())

    shifts = (end - start).days * 24 / SHIFT

    period_names = periods
    if period == 'month':
        period_names = [calendar.month_abbr[per].title() for per in periods]

    access_types = beamtime_info.values('access__name', 'access__color').order_by('access__name').annotate(count=Sum('shifts'))
    project_types = beamtime_info.values('project__kind__name').order_by('project__kind__name').annotate(count=Sum('shifts'))

    access_type_colors = {a['access__name']: a['access__color'] for a in access_types}
    project_type_colors = { p['project__kind__name']: ColorScheme.Live8[i] for i, p in enumerate(project_types)}

    period_data = defaultdict(lambda: defaultdict(int))
    for summary in beamtime_info.values(field, 'access__name').annotate(shifts=Sum('shifts')):
        period_data[summary[field]][summary['access__name']] = summary['shifts']
    for access in access_types:
        for value in period_data.values():
            if access['access__name'] not in value.keys():
                value[access['access__name']] = 0

    project_period_data = defaultdict(lambda: defaultdict(int))
    for summary in beamtime_info.values(field, 'project__kind__name').annotate(shifts=Sum('shifts')):
        project_period_data[summary[field]][summary['project__kind__name']] = summary['shifts']
    for project_type in project_types:
        for value in project_period_data.values():
            if project_type['project__kind__name'] not in value.keys():
                value[project_type['project__kind__name']] = 0

    downtime_info = beamline.downtime.with_duration().filter(**filters)
    downtime_scopes = [str(Downtime.SCOPE_CHOICES[i]) for i in range(len(Downtime.SCOPE_CHOICES))]
    downtime_data = defaultdict(lambda: defaultdict(int))
    for summary in downtime_info.values(field, 'scope').annotate(shifts=Sum('shifts')):
        downtime_data[summary[field]][str(Downtime.SCOPE_CHOICES[summary['scope']])] = summary['shifts']

    downtime_table_data = []
    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(downtime_data[per])
        downtime_table_data.append(series)

    for row in downtime_table_data:
        for k in downtime_scopes:
            if k not in row.keys():
                row[k] = 0

    downtime_table = [['{}'.format(p)] + [0]*len(downtime_table_data) + [0] for p in downtime_scopes]
    total_row = ['Total'] + [0]*len(downtime_table_data) + [0]
    for row in downtime_table:
        for i, item in enumerate(downtime_table_data):
            row[i+1] = item.get(row[0], 0)
            total_row[i+1] += row[i+1]
        row[-1] = sum(row[1:-1])
        total_row[-1] += row[-1]

    access_type_data = []
    project_type_data = []
    # beamtime histogram
    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(period_data[per])
        access_type_data.append(series)

    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(project_period_data[per])
        project_type_data.append(series)

    project_type_table = [[p['project__kind__name']] + [0]*len(project_type_data) + [0] for p in project_types]
    total_row = ['Total'] + [0]*len(project_type_data) + [0]
    for row in project_type_table:
        for i, item in enumerate(sorted(project_type_data, key=lambda x: x[period.title()])):
            row[i+1] = item.get(row[0], 0)
            total_row[i+1] += row[i+1]
        row[-1] = sum(row[1:-1])
        total_row[-1] += row[-1]

    project_type_table.append(total_row)

    access_type_table = []
    for item in access_types:
        access_counts = [period_data[per][item['access__name']] for per in periods]
        access_type_table.append([item['access__name']] + access_counts + [sum(access_counts)])
    bt_period_counts = [sum(period_data[per].values()) for per in periods]
    access_type_table.append(['Total'] + bt_period_counts + [sum(bt_period_counts)])

    stats = {
        'title': 'Beamtime Summary',
        'style': 'row',
        'content': [
            {
                'title': 'Scheduled beamtime shifts by {}'.format(period),
                'kind': 'table',
                'data': [[''] + period_names + ['All']] + access_type_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Beamtime access type shifts by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [[d['access__name'] for d in access_types]],
                    'data': access_type_data,
                    'colors': access_type_colors
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Beamtime by access type',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": [
                        {'label': str(entry['access__name']), 'value': entry['count'],
                         'color': entry['access__color']} for entry in access_types
                    ],
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Scheduled beamtime shifts by {}'.format(period),
                'kind': 'table',
                'data': [[''] + period_names + ['All']] + project_type_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Beamtime project type shifts by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [[d['project__kind__name'] for d in project_types]],
                    'data': project_type_data,
                    'colors': project_type_colors
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Beamtime by project type',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": [
                        {'label': str(entry['project__kind__name']),
                         'value': entry['count'],
                         'color': project_type_colors[entry['project__kind__name']]
                         } for entry in project_types
                    ],
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Downtime by {}'.format(period),
                'kind': 'table',
                'data': [[''] + period_names + ['All']] + downtime_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Downtime shifts by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [downtime_scopes],
                    'data': downtime_table_data,
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Beamtime by access type',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": [
                        {'label': str(entry['access__name']), 'value': entry['count'],
                         'color': entry['access__color']} for entry in access_types
                    ],
                },
                'style': 'col-12 col-md-6'
            }
        ]
    }
    return stats