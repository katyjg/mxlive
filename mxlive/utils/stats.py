from django.db.models import Count

import calendar

def generic_stats(objlist, filters, date_field=None):
    stats = {}
    if objlist:
        model = objlist.first()._meta.verbose_name_plural
        content = []
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
            period_data = {}
            for flt in filters:
                period_data[flt] = [{
                    **{period.title(): period_dict[per]},
                    **{k[flt]: k['count']
                       for k in objlist.filter(**{field: per}).values(flt).order_by(flt).annotate(count=Count('id'))}
                } for per in periods]
                options = set([k for p in period_data[flt] for k in p.keys()]).difference([period.title()])
                for opt in options:
                    for e in period_data[flt]:
                        e[opt] = e.get(opt, 0)

        for flt in filters:
            data = objlist.values(flt).order_by(flt).annotate(count=Count('id'))
            plot = {
                'title': "{} by {}".format(model.title(), flt.replace('__', ' ').title()),
                'kind': 'columnchart',
                'data': {
                    'aspect-ratio': 2,
                    'x-label': period and period.title() or flt.replace('__', ' ').title(),
                    'data': (date_field and period_data.get(flt) and period_data[flt]) or [
                        {
                            flt.replace('__', ' ').title(): str(datum[flt]),
                            "Count": datum['count'],
                        } for datum in data
                    ]
                },
                'style': 'col-12 col-md-6'
            }
            content.append(plot)
        stats = {
            'details': [
                {
                    'title': '{}{}{}'.format(model.title(), year and ' in ', year or ''),
                    'style': "row",
                    'content': content
                }
            ]
        }
    return stats