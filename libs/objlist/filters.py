from datetime import date
from django.contrib import admin


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
            choices = sorted({v['date'].year for v in model.objects.values(field_name).order_by(field_name).distinct()}, reverse=True)
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
        
    