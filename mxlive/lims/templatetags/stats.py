from collections import defaultdict
from datetime import datetime

from django import template
from django.utils.safestring import mark_safe

from mxlive.lims.models import *
from mxlive.staff.models import UserCategory
from .converter import humanize_duration
from ..stats import SHIFT, get_data_periods

register = template.Library()

COLOR_SCHEME = ["#883a6a", "#1f77b4", "#aec7e8", "#5cb85c", "#f0ad4e"]
GRAY_SCALE = ["#000000", "#555555", "#888888", "#cccccc", "#eeeeee"]


@register.simple_tag(takes_context=False)
def get_data_stats(bl, year):
    data = bl.datasets.all()
    years = get_data_periods()
    kinds = list(DataType.objects.annotate(count=Count('datasets', filter=Q(datasets__beamline=bl))).filter(count__gt=0))
    yearly_info = defaultdict(lambda: defaultdict(int))

    for summary in data.values('created__year', 'kind__name').annotate(count=Count('pk')):
        yearly_info[summary['created__year']][summary['kind__name']] = summary['count']
    yearly = []
    for k in kinds:
        kind_counts = [yearly_info[yr][k.name] for yr in years]
        yearly.append([k.name] + kind_counts + [sum(kind_counts)])
    year_counts = [sum(yearly_info[yr].values()) for yr in years]
    yearly.append(['Total'] + year_counts + [sum(year_counts)])
    histogram_data = []

    for year, counts in sorted(yearly_info.items()):
        series = {'Year': year}
        series.update(counts)
        histogram_data.append(series)

    beam_size_query = data.filter(beam_size__isnull=False)
    beam_sizes = beam_size_query.values('beam_size').annotate(count=Count('pk'))
    beam_sizes_totals = beam_size_query.count()

    data = data.filter(created__year=year)
    stats = {'details': [
        {
            'title': 'Data Summary',
            'style': "row",
            'content': [
                {
                    'title': '',
                    'kind': 'table',
                    'data': [[''] + years + ['All']] + yearly,
                    'header': 'column row',
                    'style': 'col-12'
                },
                {
                    'title': '',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'Year',
                        'data': histogram_data,
                    },
                    'style': 'col-12'
                }
            ]
        },
        {
            'title': '{} Beamline Parameters'.format(year),
            'description': 'Data Collection Parameters Summary',
            'style': 'row',
            'content': [
                {
                    'title': 'Attenuation vs. Exposure Time',
                    'kind': 'scatterplot',
                    'data': {
                        'x': ['Exposure Time (s)'] + list(data.values_list('exposure_time', flat=True)),
                        'y1': [['Attenuation (%)'] + list(data.values_list('attenuation', flat=True))],
                        'x-scale': 'pow'
                    },
                    'style': 'col-12 col-sm-6'
                } if beam_sizes_totals else {},
                {
                    'title': 'Beam Size',
                    'kind': 'pie',
                    'data': [
                        {
                            'label': "{:0.0f}".format(entry['beam_size']),
                            'value': 360 * entry['count'] / beam_sizes_totals,
                        }
                        for entry in beam_sizes
                    ],
                    'style': 'col-12 col-sm-6'
                } if beam_sizes_totals else {},
            ]
        },
        {
            'title': '',
            'style': 'row',
            'content': [
                {
                    'title': e.title(),
                    'kind': 'barchart',
                    'data': {
                        'data': [float(d) for d in data.values_list(e, flat=True) if d != None],
                    },
                    'style': 'col-12 col-sm-6'
                } for i, e in enumerate(['energy', 'exposure_time', 'attenuation'])] if data.count() else []
        }
    ]}
    return mark_safe(json.dumps(stats))


@register.simple_tag(takes_context=False)
def get_yearly_sessions(user):
    yr = timezone.localtime() - timedelta(days=365)
    return user.sessions.filter(
        pk__in=Stretch.objects.filter(end__gte=yr).values_list('session__pk', flat=True).distinct())


@register.simple_tag(takes_context=False)
def samples_per_hour(user, sessions):
    ttime = total_time(sessions, user)
    samples = sum([s.samples().count() for s in sessions])
    return round(samples / ttime, 2) if ttime else 'None'


@register.filter
def samples_per_hour_all(category):
    yr = timezone.localtime() - timedelta(days=365)
    sessions = Session.objects.filter(
        pk__in=Stretch.objects.filter(end__gte=yr).values_list('session__pk', flat=True).distinct())
    ttime = sum(
        [s.total_time() for s in sessions.filter(project__pk__in=category.projects.values_list('pk', flat=True))])
    samples = sum(
        [s.samples().count() for s in sessions.filter(project__pk__in=category.projects.values_list('pk', flat=True))])
    return round(samples / ttime, 2) if ttime else 'None'


@register.filter
def samples_per_hour_percentile(category, user):
    yr = timezone.localtime() - timedelta(days=365)
    sessions = Session.objects.filter(
        pk__in=Stretch.objects.filter(end__gte=yr).values_list('session__pk', flat=True).distinct())
    data = {project.username: {'samples': sum([s.samples().count() for s in sessions.filter(project=project)]),
                               'total_time': sum([s.total_time() for s in sessions.filter(project=project)])}
            for project in category.projects.all()}
    averages = sorted([round(v['samples'] / v['total_time'], 2) if v['total_time'] else 0 for v in data.values()])
    my_avg = round(data[user.username]['samples'] / data[user.username]['total_time'], 2) \
        if data[user.username]['total_time'] else 0

    return round((averages.index(my_avg) + 0.5 * averages.count(my_avg)) * 100 / len(averages))


@register.simple_tag(takes_context=False)
def get_project_stats(user):
    data = user.datasets.all()
    stats = {}
    years = get_data_periods()

    kinds = [k for k in DataType.objects.all() if data.filter(kind=k).exists()]
    yrs = [{'Year': yr} for yr in years]
    for yr in yrs:
        yr.update({k.name: data.filter(created__year=yr['Year'], kind=k).count() for k in kinds})
    yearly = [
        [k.name] + [data.filter(created__year=yr, kind=k).count() for yr in years] + [data.filter(kind=k).count()]
        for k in kinds]
    totals = [['Total'] + [data.filter(created__year=yr).count() for yr in years] + [data.count()]]

    """
    shifts = total_shifts(user.sessions.all(), user)
    ttime = total_time(user.sessions.all(), user)
    shutters = round(sum([d.num_frames() * d.exposure_time for d in data if d.exposure_time]), 2)/3600.

    stats = {'details': [
        {
            'title': '{} Summary'.format(user.username.title()),
            'description': 'Data Collection Summary for {}'.format(user.username.title()),
            'style': "col-12",
            'content': [
                {
                    'title': 'Time Usage',
                    'kind': 'table',
                    'data': [
                        ['Shifts Used', '{} ({})'.format(shifts, humanize_duration(shifts * SHIFT))],
                        ['Actual Time', '{} % ({})'.format(round(ttime / (shifts * SHIFT), 2), humanize_duration(ttime))],
                        ['Shutters Open', '{}'.format(humanize_duration(shutters))],
                    ],
                    'header': 'column',
                    'style': 'col-sm-6'
                },
                {
                    'title': 'Overall Statistics',
                    'kind': 'table',
                    'data': [
                        ['Sessions', user.sessions.count()],
                        ['Shipments / Containers', "{} / {}".format(
                            user.shipments.count(),
                            user.containers.filter(status__gte=Container.STATES.ON_SITE).count())],
                        ['Groups / Samples', "{} / {}".format(
                            user.groups.filter(shipment__status__gte=Shipment.STATES.ON_SITE).count(),
                            user.samples.filter(container__status__gte=Container.STATES.ON_SITE).count())],
                    ],
                    'header': 'column',
                    'style': 'col-sm-6'
                },
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
        }
        ]}
        """
    return stats


@register.simple_tag(takes_context=False)
def get_usage_stats(bl, year):
    KIND_COLORS = {"11": {"color": "#0275d8",
                          "name": '/'.join(UserCategory.objects.filter(pk__in=[1]).values_list('name', flat=True))},
                   "12": {"color": "#883a6a",
                          "name": '/'.join(UserCategory.objects.filter(pk__in=[2]).values_list('name', flat=True))},
                   "13": {"color": "#E9953B",
                          "name": '/'.join(UserCategory.objects.filter(pk__in=[3]).values_list('name', flat=True))},
                   "14": {"color": "#999999",
                          "name": '/'.join(UserCategory.objects.filter(pk__in=[4]).values_list('name', flat=True))},
                   "23": {"color": "#A28EB4",
                          "name": '/'.join(UserCategory.objects.filter(pk__in=[1, 2]).values_list('name', flat=True))},
                   "24": {"color": "#DBC814", "name": '/'.join(
                       UserCategory.objects.filter(pk__in=[1, 3]).order_by('-name').values_list('name', flat=True))},
                   "25": {"color": "#B36255",
                          "name": '/'.join(UserCategory.objects.filter(pk__in=[2, 3]).values_list('name', flat=True))}}
    sessions = bl.sessions.filter(created__year=year).order_by('project')
    datasets = bl.datasets.filter(session__in=sessions)
    data = [
        {
            'project': Project.objects.get(pk=p),  # User
            'sessions': sessions.filter(project=p).count(),  # Sessions
            'num_data': datasets.filter(kind__contains='DATA', project__pk=p).count(),  # Full Datasets
            'shutters': round(sum([d.num_frames() * d.exposure_time for d in datasets.filter(project__pk=p)]), 2),
            # Shutter Open
            'shifts': total_shifts(sessions, p),  # Shifts
            'total_time': round(total_time(sessions, p), 2),  # Total Time
            'used_time': int(total_time(sessions, p) / (total_shifts(sessions, p) * SHIFT) * 100),  # Used Time (%)
            'data_rate': round(datasets.filter(kind__contains='DATA', project__pk=p).count() / total_time(sessions, p),
                               2) if total_time(sessions, p) else 0,  # Datasets/Hour
            'samples': round(sum([s.samples().count() for s in sessions.filter(project=p)]) / total_time(sessions, p),
                             2) if total_time(sessions, p) else 0,  # Sample Rate
        }
        for p in sessions.values_list('project', flat=True).distinct()
    ]

    ttime = sum([u['total_time'] for u in data])
    shifts = len(set([y for x in [s.shifts() for s in sessions] for y in x]))
    screened = datasets.exclude(kind__contains='DATA').values_list('sample', flat=True).distinct().count()
    collected = datasets.filter(kind__contains='DATA').values_list('sample', flat=True).distinct().count()
    stats = {'details': [
        {
            'title': 'Usage Metrics',
            'style': 'col-12',
            'content': [
                {
                    'title': 'Total Activity',
                    'kind': 'table',
                    'data': [
                        ['Shifts (or parts of shifts) Used', '{} ({})'.format(shifts, humanize_duration(shifts * 8))],
                        ['Datasets Collected', datasets.filter(kind__acronym='DATA').count()],
                        ['Shutters Open', humanize_duration(sum([u['shutters'] / 3600. for u in data]))],
                        ['Samples Screened', screened],
                        ['Samples Collected', collected]],
                    'style': 'col-sm-6',
                    'header': 'column'
                },
                {
                    'title': 'Average Efficiency',
                    'kind': 'table',
                    'data': [['Actual Time Used (h)', "{} ({:.1f}%)".format(humanize_duration(ttime), ttime * 100 / (
                            shifts * 8) if shifts else 0)],

                             ['Datasets/Hour Used',
                              round(datasets.filter(kind__contains='DATA').count() / ttime, 2) if ttime else 0],
                             ['Shutters Open/Hour Used', "{:.1f}%".format(
                                 sum([u['shutters'] / 3600. for u in data]) * 100 / ttime) if ttime else 0],
                             ['Samples Screened/Hour', round(screened / ttime, 2) if ttime else 0],
                             ['Samples Collected/Hour', round(collected / ttime, 2) if ttime else 0]],
                    'style': 'col-sm-6',
                    'header': 'column'
                },
                {
                    'title': 'Average Datasets per Hour',
                    'kind': 'scatterplot',
                    'data':
                        {
                            'x': ['Actual Time Used (hours)'] + [d['total_time'] for d in data],
                            'y1': [['Number of Datasets'] + [d['num_data'] for d in data]],
                            'annotations': [{
                                'xstart': 0,
                                'xend': max([u['total_time'] for u in data] or [0]),
                                'yend': 0,
                                'ystart': max([u['total_time'] for u in data] or [0]) * datasets.filter(
                                    kind__contains='DATA').count() / ttime if ttime else 0,
                                'color': '#883a6a',
                                'display': None
                            }]
                        },
                    'description': 'The line plotted shows the average number of full datasets collected per hour.',
                    'style': 'col-sm-12'
                },
                {
                    'title': 'User Statistics',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'User',
                        'colors': GRAY_SCALE,
                        'data': [{'User': u['project'].username,
                                  'Shutters': round(u['shutters'] / 36 / u['total_time'], 2) if u['total_time'] else 0,
                                  'Samples': u['samples'],
                                  'Datasets': u['data_rate'],
                                  'Time': u['used_time'],
                                  'color': KIND_COLORS.get("{}{}".format(u['project'].categories.count(), sum(
                                      u['project'].categories.values_list('pk', flat=True))), {}).get('color', '')
                                  } for u in
                                 sorted(data, key=lambda x: x['shutters'] / x['total_time'] if x['total_time'] else 0)],
                    },
                    'notes': "&nbsp;".join(
                        ["<span class='label hover-label' style='background-color: {}; color: white;'>{}</span>".format(
                            v['color'],
                            v['name'])
                            for v in sorted(KIND_COLORS.values(), key=lambda x: x['name'])]) +
                             "<dl><dt>Shutters</dt><dd>Percentage of time used when the shutter was open</dd><dt>Samples</dt><dd>Average number of samples collected or screened per hour</dd><dt>Datasets</dt><dd>Average number of full datasets collected per hour</dd><dt>Time</dt><dd>Percentage of time used ([actual time used] / [shifts used * 8])</dd></dl>",
                    'style': 'col-sm-12'
                },
                {
                    'title': 'Datasets by Time of Week',
                    'kind': 'barchart',
                    'data': {
                        'data': [datetime.strftime(datetime(2018, 1, d.isoweekday(), d.hour, d.minute), '%c') for d in
                                 [timezone.localtime(ds.created) for ds in datasets.all()]],
                        'color': ["#883a6a"],
                        'x-scale': 'time',
                        'bins': 100,
                        'time-format': "%A %H:00"
                    },
                    'style': 'col-12'
                },
                {
                    'kind': 'table',
                    'header': 'row',
                    'data': [['User', 'Sessions', 'Shifts', 'Shutters Open',
                              'Total Time', 'Used Time (%)', 'Full Datasets', 'Full Datasets/Hour',
                              'Samples/Hour']] +
                            [[u['project'].username, u['sessions'], u['shifts'],
                              humanize_duration(u['shutters'] / 3600),
                              humanize_duration(u['total_time']), u['used_time'], u['num_data'], u['data_rate'],
                              u['samples']]
                             for u in
                             sorted(data, key=lambda x: x['total_time'] / x['shutters'] if x['shutters'] else 0)]
                }
            ]
        }
    ]}
    return mark_safe(json.dumps(stats))


@register.simple_tag(takes_context=False)
def get_session_stats(data, session):
    shutters = sum([d.exposure_time * d.num_frames() for d in data.all()]) / 3600.
    data_counts = [
        [count['key'], count['value']] for count in
        session.datasets.values(key=F('kind__name')).order_by('key').annotate(value=Count('id'))
    ]
    frame_stats = defaultdict(list)
    for info in session.datasets.values(key=F('kind__name')).values('key', 'frames'):
        size = len(info.get('frames', []))
        if size:
            frame_stats[info['key']].append(size)
    data_stats = [
        ['Avg Frames/{}'.format(key), '{:0.0f}'.format(sum(sizes) / len(sizes))]
        for key, sizes in frame_stats.items() if sizes
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
                                ['Total Time', humanize_duration(session.total_time())],
                                ['First Login',
                                 session.stretches.last() and datetime.strftime(timezone.localtime(session.start()),
                                                                                '%B %d, %Y %H:%M') or ''],
                                ['Samples', session.samples().count()]
                            ] + data_counts,
                    'header': 'column',
                    'style': 'col-4',
                },
                {
                    'title': '',
                    'kind': 'table',
                    'data': [
                                ['Shutter Open', "{} ({:.2f}%)".format(humanize_duration(hours=shutters),
                                                                       shutters * 100 / session.total_time() if session.total_time() else 0)],
                                ['Last Dataset',
                                 data.last() and datetime.strftime(timezone.localtime(data.last().modified),
                                                                   '%c') or ''],
                                ['No. of Logins', session.stretches.count()],
                            ] + data_stats,
                    'header': 'column',
                    'style': 'col-4',
                },
                {
                    'title': '',
                    'kind': 'histogram',
                    'data': {
                        'x-label': 'Type',
                        'data': [
                            {'Type': row[0], 'val': row[1]}
                            for row in data_counts],
                    },
                    'style': 'col-4'
                }

            ]
        },
    ]}
    """
            ,
            {
                'title': 'Beamline Parameters',
                'description': 'Data Collection Parameters Summary',
                'style': 'col-12',
                'content': [
                    {
                        'title': 'Attenuation vs. Exposure Time',
                        'kind': 'scatterplot',
                        'data':
                            {'x': ['Exposure Time (s)'] + [d for d in data.values_list('exposure_time', flat=True)],
                             'y1': [['Attenuation (%)'] + [d for d in data.values_list('attenuation', flat=True)]]},
                        'style': 'col-9'
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
                        'style': 'col-3'
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
                    'style': 'col-4'
                } for i, e in enumerate(['energy', 'exposure_time', 'attenuation'])] if data.count() else []
            }"""
    return mark_safe(json.dumps(stats))


@register.simple_tag(takes_context=False)
def get_session_gaps(data):
    data = data.order_by('created')
    gaps = []
    for i in range(data.count() - 1):
        if data[i].created <= (started(data[i + 1]) - timedelta(minutes=10)):
            gaps.append([data[i].created, started(data[i + 1]),
                         humanize_duration((started(data[i + 1]) - data[i].created).total_seconds() / 3600.)])
    return gaps


def js_epoch(dt):
    return int("{:0.0f}000".format(dt.timestamp() if dt else datetime.now().timestamp()))


@register.filter(takes_context=False)
def get_data_timeline(session):
    timeline = []
    for stretch in session.stretches.with_duration():
        timeline.append({
            "times": [{
                "starting_time": js_epoch(stretch.start),
                "ending_time": js_epoch(stretch.end),
                "color": "rgb(174,199,232)"
            }],
            "hover": "Beamline Stretch ({})".format(stretch.duration) if stretch.end else "Active Beamline Stretch",
        })

    for data in session.datasets.all():
        timeline.append({
            "times": [{
                "starting_time": js_epoch(started(data)),
                "ending_time": js_epoch(data.created),
                "y": data.num_frames(),
                "color": "rgb(31,119,180)"
            }],
            "hover": "{} | {}".format(data.kind, data.name)
        })

    return timeline


@register.filter
def get_years(bl):
    return sorted(
        {v['created'].year for v in Data.objects.filter(beamline=bl).values("created").order_by("created").distinct()})


@register.filter
def started(data):
    return data.modified - timedelta(seconds=(data.exposure_time * data.num_frames()))


def total_shifts(sessions, project):
    shifts = [y for x in [s.shifts() for s in sessions.filter(project=project)] for y in x]
    return len(set(shifts))


def total_time(sessions, project):
    return sum([s.total_time() for s in sessions.filter(project=project)])
