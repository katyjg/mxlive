import calendar
from collections import defaultdict

from django.conf import settings
from django.db.models import Sum, Count, Avg

from memoize import memoize

from mxlive.schedule.models import Beamtime, Downtime, AccessType
from mxlive.lims.models import ProjectType
from mxlive.lims.stats import ColorScheme

HOUR_SECONDS = 3600
SHIFT = getattr(settings, "HOURS_PER_SHIFT", 8)


@memoize(timeout=HOUR_SECONDS)
def get_beamtime_periods(period='year', beamline=None):
    field = 'start__{}'.format(period)
    filters = beamline and {'beamline': beamline} or {}
    return sorted(Beamtime.objects.filter(**filters).values_list(field, flat=True).distinct())


def beamtime_stats(beamline, period='year', **filters):
    periods = get_beamtime_periods(period=period, beamline=beamline)
    filters = {k.replace('created', 'start'): v for k, v in filters.items()}
    field = 'start__{}'.format(period)

    beamtime_info = beamline.beamtime.with_duration().filter(**filters).filter(cancelled=False)

    period_names = periods
    if period == 'month':
        period_names = [calendar.month_abbr[per].title() for per in periods]

    access_types = list(
        beamtime_info.values('access__name', 'access__color').order_by('access__name').annotate(count=Sum('shifts'), visits=Count('id')))
    for a in AccessType.objects.exclude(name__in=[v['access__name'] for v in access_types]):
        access_types.append({'access__name': a.name, 'access__color': a.color, 'count': 0, 'visits': 0})

    project_types = list(beamtime_info.values('project__kind__name').order_by('-project__kind__name').annotate(count=Sum('shifts')))
    for p in ProjectType.objects.exclude(name__in=[v['project__kind__name'] or '' for v in project_types]):
        project_types.append({'project__kind__name': p.name, 'count': 0})

    access_type_colors = {a['access__name']: a['access__color'] for a in access_types}
    project_type_colors = { p['project__kind__name']: ColorScheme.Live8[i] for i, p in enumerate(sorted(project_types, key = lambda x: x['project__kind__name'] or ''))}

    period_data = defaultdict(lambda: defaultdict(int))
    for summary in beamtime_info.values(field, 'access__name').annotate(shifts=Sum('shifts')):
        period_data[summary[field]][summary['access__name']] = summary['shifts']
    for access in access_types:
        for value in period_data.values():
            if access['access__name'] not in value.keys():
                value[access['access__name']] = 0

    visit_period_data = defaultdict(lambda: defaultdict(int))
    for summary in beamtime_info.values(field, 'access__name').annotate(shifts=Count('id')):
        visit_period_data[summary[field]][summary['access__name']] = summary['shifts']
    for access in access_types:
        for value in visit_period_data.values():
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
    cancelled_time = beamline.beamtime.with_duration().filter(**filters).filter(cancelled=True).values(field).annotate(shifts=Sum('shifts'))
    cancelled_info = {c['start__year']: c['shifts'] for c in cancelled_time}

    downtime_scopes = [str(Downtime.SCOPE_CHOICES[i]) for i in range(len(Downtime.SCOPE_CHOICES))] + ['Cancelled Shifts']
    downtime_data = defaultdict(lambda: defaultdict(int))
    for summary in downtime_info.values(field, 'scope').annotate(shifts=Sum('shifts')):
        downtime_data[summary[field]][str(Downtime.SCOPE_CHOICES[summary['scope']])] = summary['shifts']

    downtime_summary = ""
    for scope in Downtime.SCOPE_CHOICES:
        downtime_summary += ' <strong>{}</strong>'.format(scope[1]) + '\n\n'
        downtime_summary += ' Unspecified ({}) '.format(sum([s['shifts'] for s in
                                       downtime_info.filter(scope=scope[0]).filter(comments='').values(field).annotate(shifts=Sum('shifts'))]))
        downtime_summary += ' \t'.join(['{} ({})'.format(s['comments'], s['shifts']) for s in
                                       downtime_info.filter(scope=scope[0]).exclude(comments='').values(field, 'comments').annotate(shifts=Sum('shifts'))]) + '\n\n'

    downtime_table_data = []
    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(downtime_data[per])
        downtime_table_data.append(series)
    for per in downtime_table_data:
        per['Cancelled Shifts'] = cancelled_info.get(per[period.title()], 0)

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
    visit_data = []
    # beamtime histogram
    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(period_data[per])
        access_type_data.append(series)

    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(project_period_data[per])
        project_type_data.append(series)

    for i, per in enumerate(periods):
        series = {period.title(): period_names[i]}
        series.update(visit_period_data[per])
        visit_data.append(series)

    project_type_table = [[p['project__kind__name']] + [0]*len(project_type_data) + [0] for p in project_types]
    total_row = ['Total'] + [0]*len(project_type_data) + [0]
    for row in project_type_table:
        for i, item in enumerate(sorted(project_type_data, key=lambda x: x[period.title()])):
            row[i+1] = item.get(row[0], 0)
            total_row[i+1] += row[i+1]
        row[-1] = sum(row[1:-1])
        total_row[-1] += row[-1]

    project_type_table.append(total_row)

    visit_table = []
    for item in access_types:
        visit_counts = [visit_period_data[per][item['access__name']] for per in periods]
        visit_table.append([item['access__name']] + visit_counts + [sum(visit_counts)])
    visit_period_counts = [sum(visit_period_data[per].values()) for per in periods]
    visit_table.append(['Total'] + visit_period_counts + [sum(visit_period_counts)])

    access_type_table = []
    for item in access_types:
        access_counts = [period_data[per][item['access__name']] for per in periods]
        access_type_table.append([item['access__name']] + access_counts + [sum(access_counts)])
    bt_period_counts = [sum(period_data[per].values()) for per in periods]
    access_type_table.append(['Total'] + bt_period_counts + [sum(bt_period_counts)])

    stats = {
        'title': '{} Beamtime Summary'.format(beamline),
        'style': 'row',
        'content': [
            {
                'title': 'Delivered beamtime shifts by {}'.format(period),
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
                'title': 'Delivered beamtime shifts by {}'.format(period),
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
                'title': 'Delivered visits by {}'.format(period),
                'kind': 'table',
                'data': [[''] + period_names + ['All']] + visit_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Delivered visits by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [[d['access__name'] for d in access_types]],
                    'data': visit_data,
                    'colors': access_type_colors
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Delivered visits by access type',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": [
                        {'label': str(entry['access__name']), 'value': entry['visits'],
                         'color': entry['access__color']} for entry in access_types
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
                    'data': downtime_table_data,
                },
                'style': 'col-12 col-md-6'
            },
            {
                'notes': (
                    downtime_summary
                ),
                'style': 'col-12 col-md-6'
            }
        ]
    }
    return stats