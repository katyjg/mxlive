from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext as _
from datetime import datetime, timedelta
from django.utils import dateformat, timezone
from dateutil import parser

def get_week_extent(dt):
    """Given a date return the first and last dates of the week as
    a tuple"""
    year, week, day = dt.isocalendar()
    sd = dt - timedelta(days=day-1)
    ed = sd + timedelta(days=7)
    return (sd, ed)

def get_specs_for_date(date_str):
    """Get the starting and ending dates for the current week, and for the 
    previous and next week from the date given in date_str.  Each pair is a 
    tuple (start_date, end_date), and the return value contains three tuples:
    previous_week, current_week, next_week. Current_week is not the week of the 
    date in date_str but rather now().    
    """
    current = parser.parse(date_str)
    if not current:
        current = timezone.now().date()
    prev = current - timedelta(days=7)
    nxt = current + timedelta(days=7)
    return get_week_extent(prev), get_week_extent(current), get_week_extent(nxt)


class WeeklyDateFilter(SimpleListFilter):
    title = 'Week Created'
    parameter_name = 'weekof'
    field = 'created'
    
    def lookups(self, request, model_admin):
        prev_week, cur_week, next_week = get_specs_for_date(request.GET.get('weekof', None))
        return (
            (prev_week[0].strftime('%Y-%m-%d'), "%s %s" % (_('Week of'), dateformat.format(prev_week[0], 'M jS'))),
            (cur_week[0].strftime('%Y-%m-%d'), "%s %s" % (_('Week of'), dateformat.format(cur_week[0], 'M jS'))),
            (next_week[0].strftime('%Y-%m-%d'), "%s %s" % (_('Week of'), dateformat.format(next_week[0], 'M jS'))),
        )
    
    def queryset(self, request, queryset):
        dt = parser.parse(self.value())
        if not dt:
            dt = timezone.now().date()
        week_start, week_end = get_week_extent(dt)
        qs_str = {'%s__gte' % self.field: week_start,
                  '%s__lt' % self.field: week_end}
        return queryset.filter(**qs_str)
    
    