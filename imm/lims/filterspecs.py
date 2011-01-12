from django.db import models
from django.contrib.admin.filterspecs import FilterSpec, DateFieldFilterSpec
from django.utils.translation import ugettext as _
from datetime import datetime, date, timedelta
from django.utils import dateformat

def get_spec_for_week(field_name, dt, prefix=''):
    start = dt + timedelta(days=-dt.weekday())
    end = start + timedelta(days=6)
    this_dt = datetime.now().date()
    this_start = this_dt + timedelta(days=-this_dt.weekday())
    if this_start == start:
        title = _('%sThis Week' % (prefix))
    else:
        title = _('%sWeek of %s' % (prefix, dateformat.format(dt, 'M jS')))
    spec = {'%s__gte' % field_name: str(start), '%s__lte' % field_name: str(end) }
    return title, spec

def get_spec_for_day(field_name, dt, prefix=''):
    this_dt = datetime.now().date()
    yest_dt = this_dt + timedelta(days=-1)
    nxt_dt = dt + timedelta(days=1)
    if dt == this_dt:
        title = _('%sToday' % (prefix))
    elif dt == yest_dt:
        title = _('%sYesterday' % (prefix))
    else:
        title = _('%sWeek of %s' % (prefix, dateformat.format(dt, 'M jS')))
    title = _('%s%s' % (prefix, dateformat.format(dt, 'M jS')))
    spec = {'%s__gte' % field_name: str(dt), '%s__lt' % field_name: str(nxt_dt) }
    return title, spec
    
class WeeklyFilterSpec(DateFieldFilterSpec):
    """
    Adds filtering by future and previous values in the admin
    filter sidebar. Set the weekly_filter filter in the model field attribute 'weekly_filter'.

    my_model_field.weekly_filter = True
    """

    def __init__(self, f, request, params, model, model_admin):
        super(WeeklyFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.params = dict(request.GET.items())
        request_param = '%s__gte' % self.field.name
        start_day = request.GET.get(request_param, None)
        if start_day is None:
            dt = datetime.now().date()
        else:
            dt = datetime.strptime(start_day[:10],'%Y-%m-%d').date()

        nxt_dt = dt + timedelta(weeks=+1)
        prv_dt = dt + timedelta(weeks=-1)
        
        self.links = (
              get_spec_for_week(self.field.name, prv_dt, 'Previous: '),
              get_spec_for_week(self.field.name, dt),
              get_spec_for_week(self.field.name, nxt_dt, 'Next: '),
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
            dt = datetime.now().date()
        else:
            dt = datetime.strptime(start_day[:10],'%Y-%m-%d').date()

        nxt_dt = dt + timedelta(days=+1)
        prv_dt = dt + timedelta(days=-1)
        
        self.links = (
              get_spec_for_day(self.field.name, prv_dt, 'Previous: '),
              get_spec_for_day(self.field.name, dt),
              get_spec_for_day(self.field.name, nxt_dt, 'Next: '),
            )

    def title(self):
        return "Day"


# Register the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'weekly_filter', False), WeeklyFilterSpec))
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'daily_filter', False), DailyFilterSpec))
