from django.contrib import admin
from django.contrib.admin import FieldListFilter
from django.contrib.admin.options import IncorrectLookupParameters, IS_POPUP_VAR
from django.contrib.admin.utils import  get_fields_from_path, lookup_needs_distinct, prepare_lookup_value
from django.core.exceptions import SuspiciousOperation, ImproperlyConfigured
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.http import HttpResponse
from django.utils import six, timezone
from collections import OrderedDict
from django.utils.encoding import force_str, smart_str
from django.utils.http import urlencode
from django.utils.text import slugify, mark_safe
from django.views.generic import ListView
from django.core.urlresolvers import reverse_lazy
import re
import operator
import sys
import unicodecsv as csv
from HTMLParser import HTMLParser
from django.core.exceptions import FieldDoesNotExist
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'page'
SEARCH_VAR = 'q'
TO_FIELD_VAR = 't'
ERROR_FLAG = 'e'
CSV_FLAG = 'csv'
GRID_FLAG = 'grid'
IGNORED_PARAMS = (ALL_VAR, PAGE_VAR, ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, 
                  SEARCH_VAR, TO_FIELD_VAR,IS_POPUP_VAR,CSV_FLAG, GRID_FLAG)


class HTMLStripper(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def to_utf8(v):
    if isinstance(v, basestring):
        s = HTMLStripper()
        s.feed(v)
        return '{}'.format(s.get_data())
    else:
        return v


def _get_field_name(model, name):
    if not '__' in name:
        try:
            return model._meta.get_field_by_name(name)[0].verbose_name.title()
        except FieldDoesNotExist:
            return name.title()
    else:
        this, rest = name.split('__', 1)
        rmodel = model._meta.get_field_by_name(this)[0]
        return rmodel.verbose_name.title() + ':' + _get_field_name(rmodel.rel.to, rest)


class CSVResponseMixin(object):
    """
    A generic mixin that constructs a CSV response from the context data if
    the CSV export option was provided in the request.
    """
    csv_fields = []

    def get_row_values(self, obj):
        row = []

        for field_name in self.csv_fields:
            try:
                f = obj._meta.get_field(field_name)
            except models.FieldDoesNotExist:
                # For non-field list_display values, the value is either a method
                # or a property.
                try:
                    field_lookups = field_name.split('__')
                    attr = obj
                    for name in field_lookups:
                        attr = getattr(attr, name, '')

                    allow_tags = getattr(attr, 'allow_tags', True)
                    if callable(attr):
                        attr = attr()
                    if field_name in self.list_transforms:
                        result_repr = mark_safe(self.list_transforms[field_name](attr, obj))
                    else:
                        result_repr = smart_str(attr)
                except AttributeError:
                    result_repr = ''
                else:
                    # Strip HTML tags in the resulting text, except if the
                    # function has an "allow_tags" attribute set to True.
                    if not allow_tags:
                        result_repr = result_repr
            else:
                field_val = getattr(obj, f.attname)
                if field_name in self.list_transforms:
                    result_repr = mark_safe(self.list_transforms[field_name](field_val, obj))
                elif isinstance(f.rel, models.ManyToOneRel):
                    if field_val is not None:
                        try:
                            result_repr = getattr(obj, f.name)
                        except AttributeError:
                            result_repr = ''
                    else:
                        result_repr = ''

                # Dates and times are special: They're formatted in a certain way.
                elif isinstance(f, models.DateField) or isinstance(f, models.TimeField):
                    if field_val:
                        if isinstance(f, models.DateTimeField):
                            result_repr = timezone.localtime(field_val).strftime('%c')
                        elif isinstance(f, models.TimeField):
                            result_repr = field_val.strftime('%X')
                        elif isinstance(f, models.DateField):
                            result_repr = field_val.strftime('%Y-%m-%d')
                        else:
                            result_repr = ""
                    else:
                        result_repr = ''
                # Booleans are special: We use images.
                elif isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
                    result_repr = field_val
                # DecimalFields are special: Zero-pad the decimals.
                elif isinstance(f, models.DecimalField):
                    if field_val is not None:
                        result_repr = ('%%.%sf' % f.decimal_places) % field_val
                    else:
                        result_repr = ''
                # Fields with choices are special: Use the representation
                # of the choice.
                elif f.choices:
                    m_name = 'get_{0}_display'.format(field_name)
                    result_repr = getattr(obj, m_name)()
                else:
                    result_repr = smart_str(field_val)
            row.append(result_repr)
        return map(to_utf8, row)

    def render_to_response(self, context, **response_kwargs):
        """
        Creates a CSV response when requested containing the list of fields in `csv_fields`.
        If `csv_fields` is empty the default template response is returned. The CSV response
        is requested by adding a `csv=1` get parameter to the URL.
        """
        # Sniff if we need to return a CSV export
        if self.csv_fields and self.request.GET.get(CSV_FLAG):
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="%s.csv"' % slugify(context['objects_title'])

            writer = csv.writer(response, encoding='utf-8')
            # Write the data
            qs = self.get_queryset().distinct()
            headers = [_get_field_name(qs.model, n) for n in self.csv_fields]
            for i, instance in enumerate(qs.all()):
                if i == 0:
                    writer.writerow(headers)
                writer.writerow(self.get_row_values(instance))

            return response
        else:
            return super(CSVResponseMixin, self).render_to_response(context, **response_kwargs)
        
    
class FilteredListView(CSVResponseMixin, ListView):
    """
    A generic view which constructs an object change-list with list-filters,
    column sorting, searching and automatic linking to add new entries or detail pages.
    
    Attributes:
    
        list_filter : List of filters to display
        list_display: list of fields, to display in column order
        list_styles: a dictionary mapping field names in list_display to strings
            representing the styles to apply to the corresponding field cell
        list_transforms: a dictionary mapping field names to functions which transform the data
            during display, functions should take two arguments. The first is the value being transformed,
             and the second is record object. It should return safe text for display
        ordering_proxies: a dictionary mapping a method name to a database field. Used to provide sorting behaviour 
            for model methods, anchored on a field
        add_url:  a url name for creating the Add link. Leave as None to leave out the link
        add_ajax: boolean, if true, load add url using ajax 
        add_target: an id of a dom element, add url will be loaded using ajax into the dom element identified
        detail_url: a url name for linking to detail pages. The url must take a single 
            kwarg of 'pk' or the key provided by `detail_url_kwarg`
        search_fields: list of fields within which to search for records
        owner_field: name of field to use for identifying the owner.  If provided,
            the queryset will be filtered to display only objects whose owner field
            matches the currently authenticated user.
        order_by: a list of fields providing the default sort order
        list_select_related: Set list_select_related to tell Django to select related entries
            in retrieving the list of objects in the object list page. 
            This can save a bunch of database queries. Default is True.
        paginate_by: number of items per page for pagination
        detail_url_kwarg: the keyworded argument to use for detail views
        detail_target: HTML container into which detail should be loaded using Ajax rather than 
           through a redirect.
        show_header: True or False. If true, Title and tools are shown. True by default
        detail_ajax: True or False. if true, load detail url using ajax 
        grid_template: if provided, this template will be used to display each grid cell in the 
            grid view of an object list template. The template should generate HTML from the "object" 
            context variable.
    """
    list_filter = []
    list_display = []
    list_styles = {}
    ordering_proxies = {}
    list_transforms = {}
    list_title = ""
    list_select_related = True
    
    grid_template = None
    tools_template = None
    paginate_by = 20
    
    add_url = None
    add_target = ""
    add_ajax = False
    
    order_flag = None
    detail_url = None
    detail_url_kwarg = 'pk'
    detail_target = None
    detail_ajax = False
    show_header = True
    
    search_fields = []
    order_by = []
    
    owner_field = None  # name of field by which to filter for ownership

    def _get_spec_data(self, spec):
        title = spec.title
        choices = list(spec.choices(self))
        selected = [choice['display'] for choice in choices if choice['selected']][0]
        return title, choices, selected

    def get_detail_url(self, obj):
        if self.detail_url:
            return reverse_lazy(self.detail_url, kwargs={self.detail_url_kwarg: getattr(obj, self.detail_url_kwarg)})
        else:
            return None

    def get_paginate_by(self, queryset):
        if self.request.GET.get(ALL_VAR):
            return None
        else:
            return self.paginate_by

    def get_grid_template(self, obj=None):
        """Return the name of the template to use for rendering grid cells"""
        if self.grid_template:
            return self.grid_template
        else:
            return '{0}_grid.html'.format(self.model.__name__.lower())

    def get_list_title(self):
        return self.list_title or self.model._meta.verbose_name_plural.title()


    def get_row_styles(self, obj):
        return ''

    def get_row_attrs(self, obj):
        attrs = {
            'class': self.get_row_styles(obj),
            'data-detail-url': self.get_detail_url(obj)
        }
        return attrs

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(FilteredListView, self).get_context_data(**kwargs)
        # Add in a FilterSpecs 
        context['filters'] = [self._get_spec_data(spec) for spec in self.filter_specs]
        context['query_string'] = self.get_query_string(remove=[PAGE_VAR, ERROR_FLAG,CSV_FLAG])
        context['objects_title'] = self.get_list_title()
        context['object_title'] = self.model._meta.verbose_name
        context['total_objects'] = self._total_items
        if self.grid_template is not None:
            # prepare grid url and flag
            if self.grid_flag:
                context['show_grid'] = False
                context['grid_url'] = self.get_query_string(remove=[GRID_FLAG,ERROR_FLAG])               
            else:
                context['show_grid'] = True
                context['grid_url'] = self.get_query_string(new_params={GRID_FLAG:1}, remove=[ERROR_FLAG])              
            
        context['headers'] = list(self.get_headers())
        if self.csv_fields:      
            context['csv_url'] = self.get_query_string(new_params={CSV_FLAG:1, ALL_VAR:1}, remove=[PAGE_VAR, ERROR_FLAG])
        return context

    def get_queryset(self):
        qs = super(FilteredListView, self).get_queryset().filter()
        if self.owner_field:
            qs = qs.filter(**{self.owner_field: self.request.user})
        self._total_items = qs.count()
        self.model = qs.model
        self._params = dict(self.request.GET.items())
        self.query = self._params.get(SEARCH_VAR, '')
        self.order_flag = self._params.get(ORDER_VAR, '')
        self.grid_flag = GRID_FLAG in self._params

        # remove IGNORED_PARAMS
        for flag in IGNORED_PARAMS:
            if flag in self._params:
                del self._params[flag]

        # First, we collect all the declared list filters.
        (self.filter_specs, self.has_filters, remaining_lookup_params,
         filters_use_distinct) = self.get_filters(self.request)

        # Then, we let every list filter modify the queryset to its liking.
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(self.request, qs)
            if new_qs is not None:
                qs = new_qs
        try:
            # apply the remaining lookup parametersthat haven't already been processed 
            qs = qs.filter(**remaining_lookup_params)
        except (SuspiciousOperation, ImproperlyConfigured):
            # Re-raised as-is so that the caller can treat them in a special way.
            raise
        except Exception as e:
            # Naked except, no other way of validating lookup parameters. 
            raise IncorrectLookupParameters(e)

        if not qs.query.select_related:
            qs = self.apply_select_related(qs)

        # Set ordering.
        ordering = self.get_ordering()
        qs = qs.order_by(*ordering)

        # Apply search results
        qs, search_use_distinct = self.get_search_results(self.request, qs, self.query)
                
        # Remove duplicates from results, if necessary   
        return qs.distinct()
        

    def apply_select_related(self, qs):
        if self.list_select_related is True:
            return qs.select_related()

        if self.list_select_related is False:
            if self.has_related_field_in_list_display():
                return qs.select_related()

        if self.list_select_related:
            return qs.select_related(*self.list_select_related)
        return qs

    def has_related_field_in_list_display(self):
        lookup_opts = self.model._meta
        for field_name in self.list_display:
            try:
                field = lookup_opts.get_field(field_name)
            except models.FieldDoesNotExist:
                pass
            else:
                if isinstance(field.rel, models.ManyToOneRel):
                    return True
        return False
        
    def get_filters(self, request):
        lookup_params = self._params
        lookup_opts = self.model._meta
        use_distinct = False

        # Normalize the types of keys
        for key, value in lookup_params.items():
            list_names = [f if isinstance(f, basestring) else f.parameter_name for f in self.list_filter]
            if not key.startswith(tuple(list_names)): # ignore keys not in list_filter
                del lookup_params[key]
                continue

            if not isinstance(key, basestring):
                # 'key' will be used as a keyword argument later must be 'str'
                del lookup_params[key]
                lookup_params[force_str(key)] = value

        filter_specs = []
        if self.list_filter:
            for list_filter in self.list_filter:
                if callable(list_filter):
                    # This is simply a custom list filter class.
                    spec = list_filter(request, lookup_params,
                        self.model, None)
                else:
                    field_path = None
                    if isinstance(list_filter, (tuple, list)):
                        # Custom FieldListFilter class for a given field.
                        field, field_list_filter_class = list_filter
                    else:
                        # Field name, so use the default registered FieldListFilter
                        field, field_list_filter_class = list_filter, FieldListFilter.create
                    if not isinstance(field, models.Field):
                        field_path = field
                        field = get_fields_from_path(self.model, field_path)[-1]
                    model_admin = admin.ModelAdmin(self.model, admin.site)
                    spec = field_list_filter_class(field, request, lookup_params,
                        self.model, model_admin, field_path=field_path)
                    # Check if we need to use distinct()
                    use_distinct = (use_distinct or
                                    lookup_needs_distinct(lookup_opts,
                                                          field_path))
                if spec and spec.has_output():
                    filter_specs.append(spec)

        # All the parameters used by the various ListFilters have been removed
        # lookup_params, now only contains other parameters passed via the query string.
        # We now loop through the remaining parameters both to ensure that all the parameters are valid
        # fields and to determine if at least one of them needs distinct(). If
        # the lookup parameters aren't real fields, then bail out.
        try:
            for key, value in lookup_params.items():
                lookup_params[key] = prepare_lookup_value(key, value)
                use_distinct = (use_distinct or
                                lookup_needs_distinct(lookup_opts, key))
            return filter_specs, bool(filter_specs), lookup_params, use_distinct
        except FieldDoesNotExist as e:
            six.reraise(IncorrectLookupParameters, IncorrectLookupParameters(e), sys.exc_info()[2])

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None: new_params = {}
        if remove is None: remove = []
        p = dict(self.request.GET.items())
        remove.extend([PAGE_VAR, ERROR_FLAG])
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))
            
    def _get_default_ordering(self):
        ordering = []
        if self.order_by:
            ordering = self.order_by
        else:
            ordering = self.lookup_opts.ordering
        return ordering

    def get_ordering_field(self, field_name):
        """
        Returns the proper model field name corresponding to the given
        field_name to use for ordering. field_name must be the name of a
        proper model field.
        """
        lookup_opts = self.model._meta
        try:
            field = lookup_opts.get_field(field_name)
            return field.name
        except models.FieldDoesNotExist:
            return None

    def get_ordering(self):
        """
        Returns the list of ordering fields for the object list.
        First we check the object's default ordering. Then, any manually-specified ordering
        from the query string overrides anything. Finally, a deterministic
        order is guaranteed by ensuring the primary key is used as the last
        ordering field.
        """
        ordering = list(self._get_default_ordering())
        if self.order_flag:
            # Clear ordering and used params
            ordering = []
            order_params = self.order_flag.split('.')
            for p in order_params:
                try:
                    pfx, idx = p.rpartition('-')[1:]
                    field_name = self.list_display[int(idx)]
                    pxy = self.ordering_proxies.get(field_name, field_name) # translate
                    order_field = self.get_ordering_field(pxy)
                    if not order_field:
                        continue # No 'admin_order_field', skip it
                    ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue # Invalid ordering specified, skip it.

#         # Add the given query's ordering fields, if any.
#         ordering.extend(queryset.query.order_by)

        # Ensure that the primary key is systematically present in the list of
        # ordering fields so we can guarantee a deterministic order across all
        # database backends.

        if not (set(ordering) & set(['pk', '-pk'])):
            # The two sets do not intersect, meaning the pk isn't present. So
            # we add it.
            ordering.append('-pk')
        return ordering

    def get_ordering_field_columns(self):
        """
        Returns a OrderedDict of ordering field column numbers and asc/desc
        """
        # We must cope with more than one column having the same underlying sort
        # field, so we base things on column numbers.
        ordering = self._get_default_ordering()
        ordering_fields = OrderedDict()
        if ORDER_VAR not in self._params:
            # for ordering specified on model Meta, we don't know
            # the right column numbers absolutely, because there might be more
            # than one column associated with that ordering, so we guess.
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for index, attr in enumerate(self.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in self._params[ORDER_VAR].split('.'):
                pfx, idx = p.rpartition('-')[1:]
                try:
                    idx = int(idx)
                except ValueError:
                    continue # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields
        
    def get_search_results(self, request, queryset, search_term):
        # Apply keyword searches.
        lookup_opts = self.model._meta
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        use_distinct = False
        if self.search_fields and search_term:

            orm_lookups = [construct_search(str(search_field))
                           for search_field in self.search_fields]
            for bit in search_term.split():
                or_queries = [models.Q(**{orm_lookup: bit})
                              for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))
            if not use_distinct:
                for search_spec in orm_lookups:
                    if lookup_needs_distinct(lookup_opts, search_spec):
                        use_distinct = True
                        break

        return queryset, use_distinct

    def get_headers(self):
        """
        Generate headers for each field in `list_display`. The header is a dictionary
        with fields `text`, which contains the text to display and optionally `style`,
        which contains the corresponding style from `list_styles`.
        
        Generate urls for multi-sorting. The urls work as a 3-state toggle in the order
        of sort-ascending, sort-descending, do not sort by column -- that is, remove 
        column from multi-sort specification.
        """  
        
        order_specs = OrderedDict([(int(re.sub(r"\D","",c)), '-' if c[0] == '-' else '') for c in self.order_flag.split('.') if c])
        
        if not self.list_display:
            yield {'text': self.model._meta.verbose_name.title()}
            
        for i, field_name in enumerate(self.list_display):
            # generate new url for sorting through the table header
            # '': sorted asc, '-':sorted desc, '*': not sorted (ignore tag)
            _sort_style = {'-': 'sorted-dn', '':'sorted-up', '*': 'not-sorted'}[order_specs.get(i, '*')]
            _field_tag = ({'':'-', '-':'*', '*':''}[order_specs.get(i, '*')], i)
            _rest_tags = [(v,k) for k,v in order_specs.items() if k != i]
            _sort_val = '.'.join(['{0}{1}'.format(d,c) for d,c in [_field_tag] + _rest_tags if d != '*'])
            _header_url = self.get_query_string(new_params={ORDER_VAR:_sort_val}, remove=[ERROR_FLAG])
                
            try:
                f = self.model._meta.get_field(field_name)
            except models.FieldDoesNotExist:
                # For non-field list_display values, check for the function
                # attribute "short_description". If that doesn't exist, fall back
                # to the method name. 

                field_lookups = field_name.split('__')
                attr = self.model
                for name in field_lookups:
                    attr = getattr(attr, name, '')
                #attr = getattr(self.model, field_name) # Let AttributeErrors propagate.
                try:
                    header = attr.short_description.title()
                except AttributeError:
                    header = field_name.replace('_', ' ').title()

                if self.ordering_proxies.get(field_name):
                    hdr = {
                        "text": header, 
                        'style': '{0} {1}'.format(self.list_styles.get(field_name, ''), _sort_style),
                        'url': _header_url
                    }
                else:
                    hdr = {
                        "text": header, 
                        'style': self.list_styles.get(field_name, '')
                    }
                yield hdr
                continue
            else:
                if isinstance(f.rel, models.ManyToOneRel) and f.null:
                    yield {"text": f.verbose_name.title(), 
                           'style': '{0} {1}'.format(self.list_styles.get(field_name, ''), _sort_style), 
                           'url': _header_url}
                    continue
                else:
                    header = f.verbose_name.title()
            yield {"text": header, 
                   'style': '{0} {1}'.format(self.list_styles.get(field_name, ''), _sort_style), 
                   'url': _header_url
                   }
     
