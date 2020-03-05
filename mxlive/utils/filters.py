from datetime import date
from django.contrib import admin
from django.utils import timezone

import calendar


class DATE_LIMIT(object):
    LEFT = -1
    RIGHT = 1
    BOTH = 0


def DateLimitFilterFactory(model, field_name='date', filter_title='Start date', limit=0):
    class DateLimitListFilter(admin.SimpleListFilter):
        title = filter_title
        parameter_name = '{0}{1}'.format(field_name,
                                         {DATE_LIMIT.LEFT: '_gte',
                                          DATE_LIMIT.RIGHT: '_lte'}.get(limit, ''))

        def lookups(self, request, model_admin):
            choices = sorted({v[field_name].year for v in model.objects.values(field_name).order_by(field_name).distinct()},
                             reverse=True)
            return ((yr, '{0}'.format(yr)) for yr in choices)

        def queryset(self, request, queryset):
            flt = {}
            if self.value() and limit <= DATE_LIMIT.BOTH:
                dt = date(int(self.value()), 1, 1)
                flt[field_name + '__gte'] = dt
            if self.value() and limit >= DATE_LIMIT.RIGHT:
                dt = date(int(self.value()), 12, 31)
                flt[field_name + '__lte'] = dt

            return queryset.filter(**flt)

    return DateLimitListFilter


def YearFilterFactory(field_name='created', start=None, end=None, reverse=True):
    end = end if end else timezone.now().year
    start = start if start else end - 15

    class YearFilter(admin.SimpleListFilter):
        parameter_name = '{}_year'.format(field_name)
        title = parameter_name.replace('_', ' ').title()

        def lookups(self, request, model_admin):
            choices = range(start, end+1) if not reverse else reversed(range(start, end+1))
            return ((yr, '{0}'.format(yr)) for yr in choices)

        def queryset(self, request, queryset):
            flt = {} if not self.value() else {'{}__year'.format(field_name): self.value()}
            return queryset.filter(**flt)

    return YearFilter


def MonthFilterFactory(field_name='created'):

    class MonthFilter(admin.SimpleListFilter):
        parameter_name = '{}_month'.format(field_name)
        title = parameter_name.replace('_', ' ').title()

        def lookups(self, request, model_admin):
            return ((month, calendar.month_name[month]) for month in range(1, 13))

        def queryset(self, request, queryset):
            flt = {} if not self.value() else {'{}__month'.format(field_name): self.value()}
            return queryset.filter(**flt)

    return MonthFilter


def QuarterFilterFactory(field_name='created'):

    class QuarterFilter(admin.SimpleListFilter):
        parameter_name = '{}_quarter'.format(field_name)
        title = parameter_name.replace('_', ' ').title()

        def lookups(self, request, model_admin):
            return ((i+1, 'Q{}'.format(i+1)) for i in range(4))

        def queryset(self, request, queryset):
            flt = {} if not self.value() else {'{}__quarter'.format(field_name): self.value()}
            return queryset.filter(**flt)

    return QuarterFilter
