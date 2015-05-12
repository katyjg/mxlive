from django.db import models
from django.contrib.admin.filterspecs import FilterSpec, DateFieldFilterSpec
from django.utils.translation import ugettext as _
from datetime import datetime

class IsActiveFilterSpec(FilterSpec):
    """
    Adds filtering by future and previous values in the admin
    filter sidebar. Set the is_active_filter filter in the model field attribute 'is_active_filter'.
    
    my_model_field.is_active_filter = True
    """
    
    def __init__(self, f, request, params, model, model_admin):
        super(IsActiveFilterSpec, self).__init__(f, request, params, model, model_admin)
        today = datetime.now()
        self.removes = {
            'Submitted': ['%s__gte' % self.field.name, '%s__lt' % self.field.name],
            'Active': ['%s__lt' % self.field.name, '%s__isnull' % self.field.name],
            'Expired': ['%s__gte' % self.field.name, '%s__isnull' % self.field.name],
            'All': ['%s__gte' % self.field.name, '%s__lt' % self.field.name, '%s__isnull' % self.field.name]}
        
        self.links = (
          (_('All'), {}),
          (_('Active'), {'%s__gte' % self.field.name: str(today), }),
          (_('Expired'), {'%s__lt' % self.field.name: str(today), }),
          (_('Submitted'), {'%s__isnull' % self.field.name: True, }),
        )
        
        if request.GET.has_key('%s__lt' % self.field.name):
            self.ttl = 'Expired'
        elif request.GET.has_key('%s__gte' % self.field.name):
            self.ttl = 'Active'
        elif request.GET.has_key('%s__isnull' % self.field.name):
            self.ttl = 'Submitted'
        else:
            self.ttl = 'All'
    
    def choices(self, cl):
        for title, param_dict in self.links:
            yield {'selected': title == self.ttl,
                   'query_string': cl.get_query_string(param_dict, self.removes[title]),
                   'display': title}

    def title(self):
        return "Status"

# Register the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'is_active_filter', False), IsActiveFilterSpec))                                  