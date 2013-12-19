from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext as _
from datetime import datetime, timedelta
from django.utils import dateformat, timezone

def get_week_extent(date_str):
    """Given a date in date_str, return the first and last dates of the week as
    a tuple"""
    dt = datetime.strptime(date_str[:10],'%Y-%m-%d').date()
    show_sd = dt + timedelta(days=-dt.weekday())
    show_ed = show_sd + timedelta(days=6)
    return (show_sd, show_ed)

def get_specs_for_date(date_str):
    """Get the starting and ending dates for the current week, and for the 
    previous and next week from the date given in date_str.  Each pair is a 
    tuple (start_date, end_date), and the return value contains three tuples:
    previous_week, current_week, next_week. Current_week is not the week of the 
    date in date_str but rather now().    
    """
    show_sd = get_week_extent(date_str)[0]
    cur_sd = timezone.now().date()
    cur_sd = cur_sd +  timedelta(days=-cur_sd.weekday())
    nxt_sd = show_sd + timedelta(weeks=+1)
    prv_sd = show_sd + timedelta(weeks=-1)
    
    cur_ed = cur_sd + timedelta(days=6)
    nxt_ed = nxt_sd + timedelta(days=6)
    prv_ed = prv_sd + timedelta(days=6)          
    return ((prv_sd, prv_ed), (cur_sd, cur_ed), (nxt_sd, nxt_ed))
   
class WeeklyDateFilter(SimpleListFilter):
    title = 'created'
    parameter_name = 'weekof'
    field = 'created'
    
    def lookups(self, request, model_admin):
        prev_week, cur_week, next_week = get_specs_for_date(self.value())
        return (
            (prev_week[0].strftime('%Y-%m-%d'), dateformat.format(prev_week[0], 'Week of M jS')),
            (cur_week[0].strftime('%Y-%m-%d'), _('This Week')),
            (next_week[0].strftime('%Y-%m-%d'), dateformat.format(next_week[0], 'Week of M jS')),
        )
    
    def queryset(self, request, queryset):
        week_start, week_end = get_week_extent(self.value())
        qs_str = {'%s_gte' % self.field: week_start,
                  '%s_lte' % self.field: week_end,}
        return queryset.filter(**qs_str)