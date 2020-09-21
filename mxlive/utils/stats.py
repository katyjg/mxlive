from django.db.models import Count

import calendar

def generic_stats(objlist, filters, date_field=None):
    stats = {}
    if objlist:
        model = objlist.first()._meta.verbose_name_plural
        content = []
        data = {}
        options = {}
        period, year = (None, None)
        if date_field:
            period = 'year'
            field = "{}__{}".format(date_field, period)
            periods = sorted(objlist.values_list(field, flat=True).order_by(field).distinct())
            if len(periods) == 1:
                year = periods[0]
                period = 'month'
                periods = [i for i in range(1, 13)]
                field = "{}__{}".format(date_field, period)
            period_dict = {per: period == 'year' and per or calendar.month_abbr[per].title() for per in periods}
            for flt in filters:
                data[flt] = [{
                    **{period.title(): period_dict[per]},
                    **{str(k[flt]): k['count']
                       for k in objlist.filter(**{field: per}).values(flt).order_by(flt).annotate(count=Count('id'))}
                } for per in periods]
                options[flt] = set([k for p in data[flt] for k in p.keys()]).difference([period.title()])
                for opt in options[flt]:
                    for e in data[flt]:
                        e[opt] = e.get(opt, 0)
        else:
            for flt in filters:
                data[flt] = [
                    {
                        flt.replace('__', ' ').title(): str(datum[flt]),
                        "Count": datum['count'],
                    } for datum in objlist.values(flt).order_by(flt).annotate(count=Count('id'))
                ]
                options[flt] = set([k for p in data[flt] for k in p.keys()])
                print(options)


        for flt in filters:
            plot = {
                'title': "{} by {}".format(model.title(), flt.replace('__', ' ').title()),
                'kind': 'columnchart',
                'data': {
                    'aspect-ratio': 2,
                    'stack': [list(set([k for p in data[flt] for k in p.keys()]))],
                    'x-label': period and period.title() or flt.replace('__', ' ').title(),
                    'data': data.get(flt, [])
                },
                'style': 'col-12 col-md-6'
            }
            content.append(plot)
        stats = {
            'details': [
                {
                    'title': '{}{}{}'.format(model.title(), year and ' in ' or '', year or ''),
                    'style': "row",
                    'content': content
                }
            ]
        }
    return stats