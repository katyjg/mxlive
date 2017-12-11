from django import template
from django.utils.safestring import mark_safe

from lims.models import *

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