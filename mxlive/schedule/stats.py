import calendar
from collections import defaultdict

from django.conf import settings
from django.db.models import Sum, Count, Avg

from memoize import memoize

from mxlive.schedule.models import Beamtime, Downtime, AccessType
from mxlive.lims.models import Project, ProjectType
from mxlive.lims.stats import ColorScheme
from mxlive.utils.functions import Median

HOUR_SECONDS = 3600
SHIFT = getattr(settings, "HOURS_PER_SHIFT", 8)
PUBLICATIONS = getattr(settings, "LIMS_USE_PUBLICATIONS", False)


@memoize(timeout=HOUR_SECONDS)
def get_beamtime_periods(period='year', beamline=None):
    field = 'start__{}'.format(period)
    filters = beamline and {'beamline': beamline} or {}
    return sorted(Beamtime.objects.filter(**filters).values_list(field, flat=True).distinct())


def make_table(data, columns, rows, total_col=True, total_row=True):
    ''' Converts a list of dictionaries into a list of lists ready for displaying as a table
        data: list of dictionaries (one dictionary per column header)
        columns: list of column headers to display in table, ordered the same as data
        rows: list of row headers to display in table
    '''
    header_row = [''] + columns
    if total_col: header_row += ['All']
    table_data = [[str(r)] + [0] * (len(header_row) - 1) for r in rows]
    for row in table_data:
        for i, val in enumerate(data):
            row[i+1] = val.get(row[0], 0)
        if total_col:
            row[-1] = sum(row[1:-1])
    if total_row:
        footer_row = ['Total'] + [0] * (len(header_row) - 1)
        for i in range(len(footer_row)-1):
            footer_row[i+1] = sum([d[i+1] for d in table_data])
    return [header_row] + table_data + [footer_row]


def beamtime_stats(beamline, period='year', **filters):
    periods = get_beamtime_periods(period=period, beamline=beamline)
    filters = {k.replace('created', 'start'): v for k, v in filters.items()}
    field = 'start__{}'.format(period)

    beamtime_info = beamline.beamtime.with_duration().filter(**filters).filter(cancelled=False)

    period_names = periods
    if period == 'month':
        period_names = [calendar.month_abbr[per].title() for per in periods]

    #Delivered beamtime by access type
    access_colors = {a.name: a.color for a in AccessType.objects.all()}
    access_names = list(access_colors.keys())

    access_info = beamtime_info.values(field, 'access__name').annotate(shifts=Sum('shifts'), visits=Count('id'))
    access_shift_data = defaultdict(lambda: defaultdict(int))
    access_visit_data = defaultdict(lambda: defaultdict(int))
    for entry in access_info:
        access_shift_data[entry[field]][str(entry['access__name'])] = entry['shifts']
        access_visit_data[entry[field]][str(entry['access__name'])] = entry['visits']

    access_shift_data = sorted([{
        **{period.title(): key},
        **{kind: data.get(kind, 0) for kind in access_names}
    } for key, data in access_shift_data.items()], key=lambda x: x[period.title()])
    access_visit_data = sorted([{
        **{period.title(): key},
        **{kind: data.get(kind, 0) for kind in access_names}
    } for key, data in access_visit_data.items()], key=lambda x: x[period.title()])
    access_shift_pie = [
        {'label': kind, 'value': sum([a[kind] for a in access_shift_data]), 'color': color}
        for kind, color in access_colors.items()]
    access_visit_pie = [
        {'label': kind, 'value': sum([a[kind] for a in access_visit_data]), 'color': color}
        for kind, color in access_colors.items()]
    access_shift_table = make_table(access_shift_data, period_names, access_names)
    access_visit_table = make_table(access_visit_data, period_names, access_names)

    # Delivered beamtime by project type
    project_colors = {p.name: ColorScheme.Live8[i+1] for i, p in enumerate(list(ProjectType.objects.order_by('name')))}
    project_colors['None'] = ColorScheme.Live8[0]
    project_names = list(project_colors.keys())

    project_info = beamtime_info.values(field, 'project__kind__name').annotate(shifts=Sum('shifts'))
    project_shift_data = defaultdict(lambda: defaultdict(int))
    for entry in project_info:
        project_shift_data[entry[field]][str(entry['project__kind__name'])] = entry['shifts']

    project_shift_data = sorted([{
        **{period.title(): key},
        **{kind: data.get(kind, 0) for kind in project_names}
    } for key, data in project_shift_data.items()], key=lambda x: x[period.title()])
    project_shift_pie = [
        {'label': kind, 'value': sum([a[kind] for a in project_shift_data]), 'color': color}
        for kind, color in project_colors.items()]
    project_shift_table = make_table(project_shift_data, period_names, project_names)

    # Distinct Users
    distinct_users_info = beamtime_info.exclude(project__isnull=True).values(field, 'project__kind__name').annotate(Count('project', distinct=True))
    distinct_users = []
    for i, per in enumerate(periods):
        series = {
            **{ period.title(): period_names[i] },
            **{ str(d['project__kind__name']): d['project__count']
                for d in distinct_users_info if d[field] == per
            }
        }
        for project_type in project_names - series.keys():
            series[str(project_type)] = 0
        distinct_users.append(series)
    distinct_user_table = make_table(distinct_users, period_names, project_names, total_col=False)

    if PUBLICATIONS:
        # Average H-index
        active_users = Project.objects.filter(pk__in=beamtime_info.values_list('project', flat=True).distinct())

    # Median of Beamtime Usage
    beamtime_usage_median = beamtime_info.values('project').annotate(beamtime=Sum('shifts')).aggregate(Median('beamtime'))
    beamtime_usage_data = {
        period_names[i]: beamtime_info.filter(**{field: per}).values('project').annotate(beamtime=Sum('shifts')).aggregate(
                   Median('beamtime'))['beamtime__median']
        for i, per in enumerate(periods)
    }

    # Downtime
    downtime_info = beamline.downtime.with_duration().filter(**filters)
    cancelled_time = beamline.beamtime.with_duration().filter(**filters).filter(cancelled=True).values(field).annotate(shifts=Sum('shifts'))
    cancelled_info = {c[field]: c['shifts'] for c in cancelled_time}

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
    downtime_table = make_table(downtime_table_data, period_names, downtime_scopes)

    stats = {
        'title': '{} Beamtime by Access Type'.format(beamline),
        'style': 'row',
        'content': [
            {
                'title': 'Delivered shifts by {}'.format(period),
                'kind': 'table',
                'data': access_shift_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Delivered shifts by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [access_names],
                    'data': access_shift_data,
                    'colors': access_colors
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Delivered shifts',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": access_shift_pie,
                },
                'style': 'col-12 col-sm-6'
            },
            {
                'title': 'Delivered visits by {}'.format(period),
                'kind': 'table',
                'data': access_visit_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Delivered visits by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [access_names],
                    'data': access_visit_data,
                    'colors': access_colors
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Delivered visits',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": access_visit_pie,
                },
                'style': 'col-12 col-sm-6'
            },
            {
                'title': 'Delivered shifts by {}'.format(period),
                'kind': 'table',
                'data': project_shift_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Delivered shifts by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [project_names],
                    'data': project_shift_data,
                    'colors': project_colors
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Beamtime by project type',
                'kind': 'pie',
                'data': {
                    "colors": "Live16",
                    "data": project_shift_pie,
                },
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Distinct Users by {}'.format(period),
                'kind': 'table',
                'data': distinct_user_table,
                'header': 'column row',
                'style': 'col-12'
            },
            {
                'title': 'Distinct Users by {}'.format(period),
                'kind': 'columnchart',
                'data': {
                    'x-label': period.title(),
                    'stack': [project_names],
                    'data': [
                        { **data,
                          **{"Median of Beamtime Usage": beamtime_usage_data[data[period.title()]]} } for data in distinct_users
                    ],
                    'colors': project_colors,
                    'line': "Median of Beamtime Usage",
                },
                'notes': 'Overall Median of Beamtime Usage: {} shifts'.format(beamtime_usage_median['beamtime__median']),
                'style': 'col-12 col-md-6'
            },
            {
                'title': 'Downtime by {}'.format(period),
                'kind': 'table',
                'data': downtime_table,
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