from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext as _
from datetime import datetime, date, timedelta
from django.utils import dateformat, timezone

def get_spec_for_week(field_name, dt, showing=None):
    start = dt + timedelta(days=-dt.weekday())
    end = start + timedelta(days=6)
    this_dt = timezone.now().date()
    this_start = this_dt + timedelta(days=-this_dt.weekday())
       
    if this_start == start:
        title = _('This Week')
    else:
        title = _('Week of %s' % (dateformat.format(dt, 'M jS')))
        
    spec = {'%s__gte' % field_name: str(start), '%s__lte' % field_name: str(end) }
    if showing is not None:
        start_showing = showing + timedelta(days=-showing.weekday())
        if start_showing == start:
            spec = {}
    return spec, title

def get_spec_for_day(field_name, dt, showing=None):
    this_dt = timezone.now().date()
    yest_dt = this_dt + timedelta(days=-1)
    nxt_dt = dt + timedelta(days=1)
    if dt == this_dt:
        title = _('Today')
    elif dt == yest_dt:
        title = _('Yesterday')
    else:
        title = dateformat.format(dt, 'M jS')
    spec = {'%s__gte' % field_name: str(dt), '%s__lt' % field_name: str(nxt_dt) }
    if showing is not None:
        if dt == showing:
            spec = {}
    return spec, title
    
class WeeklyCreatedFilter(SimpleListFilter):
    def lookups(self, request, model_admin):
        return (
            ('thisweek'),
        )
    def __init__(self, f, request, params, model, model_admin):
        super(WeeklyFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.params = dict(request.GET.items())
        request_param = '%s__gte' % self.field.name
        start_day = request.GET.get(request_param, None)
        if start_day is None:
            dt = timezone.now().date()
            showing = None
        else:
            dt = datetime.strptime(start_day[:10],'%Y-%m-%d').date()
            showing = dt

        nxt_dt = dt + timedelta(weeks=+1)
        prv_dt = dt + timedelta(weeks=-1)
        
        self.links = (
              get_spec_for_week(self.field.name, prv_dt, showing),
              get_spec_for_week(self.field.name, dt, showing),
              get_spec_for_week(self.field.name, nxt_dt, showing),
            )

    def title(self):
        return self.field.verbose_name

class DailyFilterSpec(DateFieldFilterSpec):
    """
    Adds filtering by future and previous values in the admin
    filter sidebar. Set the weekly_filter filter in the model field attribute 'daily_filter'.

    my_model_field.daily_filter = True
    """

    def __init__(self, f, request, params, model, model_admin):
        super(DailyFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.params = dict(request.GET.items())
        request_param = '%s__gte' % self.field.name
        start_day = request.GET.get(request_param, None)
        if start_day is None:
            showing = None
            dt = timezone.now().date()
        else:
            dt = datetime.strptime(start_day[:10],'%Y-%m-%d').date()
            showing = dt

        nxt_dt = dt + timedelta(days=+1)
        prv_dt = dt + timedelta(days=-1)
        
        self.links = (
              get_spec_for_day(self.field.name, prv_dt, showing),
              get_spec_for_day(self.field.name, dt, showing),
              get_spec_for_day(self.field.name, nxt_dt, showing),
            )

    def title(self):
        return "Day"


# Register the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'weekly_filter', False), WeeklyFilterSpec))
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'daily_filter', False), DailyFilterSpec))
