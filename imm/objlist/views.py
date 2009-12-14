# Create your views here.
from django.core.paginator import Paginator, QuerySetPaginator, InvalidPage
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist, PermissionDenied
from django.contrib.admin.filterspecs import FilterSpec
from django.utils.encoding import force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.db import models
from django.db.models.query import QuerySet
import operator
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.contrib.admin.options import IncorrectLookupParameters

MAX_SHOW_ALL_ALLOWED = 200
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
ERROR_FLAG = 'e'
IS_POPUP_VAR = 'pop'
TO_FIELD_VAR = 't'
   
    

class ObjectLister(ChangeList):
    def __init__(self, request, manager):
        self.manager = manager
        self.model = self.manager.model
        self.object_type = self.model.__name__
        self.opts = self.model._meta
        
        # initialize variables
        self.model_admin = admin.site._registry[self.model]
        self.root_query_set = self.model_admin.queryset(request)
        self.list_filter = self.model_admin.list_filter
        self.list_select_related = self.model_admin.list_select_related
        self.list_display = self.model_admin.list_display
        self.search_fields = self.model_admin.search_fields
        self.list_per_page = self.model_admin.search_fields
        self.lookup_opts = self.opts
        
        # Get search parameters from the query string.
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.show_all = ALL_VAR in request.GET
        self.is_popup = IS_POPUP_VAR in request.GET
        self.to_field = request.GET.get(TO_FIELD_VAR)
        self.params = dict(request.GET.items())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if TO_FIELD_VAR in self.params:
            del self.params[TO_FIELD_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]

        self.order_field, self.order_type = self.get_ordering()
        self.query = request.GET.get(SEARCH_VAR, '')
        self.query_set = self.get_query_set()
            
        self.get_results(request)
        self.title = self.opts.verbose_name
        self.filter_specs, self.has_filters = self.get_filters(request)
        self.query_string = self.get_query_string()
        
    def get_results(self, request):
        paginator = QuerySetPaginator(self.query_set, self.list_per_page)
        # Get the number of objects, with admin filters applied.
        self.paginator = paginator
        self.total_count = self.manager.count()   
        self.has_search = self.paginator.count < self.total_count
        self.header_list = self.get_headers()
        try:
            self.page_obj = paginator.page(self.page_num)
        except InvalidPage:
            self.is_paginated = False
            self.page_obj = None
            self.object_list = self.query_set.all()
        else:
            self.is_paginated = True
            self.object_list = self.page_obj.object_list 
        
    def get_ordering1(self):
        opts, params = self.opts, self.params
        # For ordering, first check the "ordering" parameter in the admin options,
        # then check the object's default ordering. If neither of those exist,
        # order descending by ID by default. Finally, look for manually-specified
        # ordering from the query string.
        ordering = opts.ordering or ['-' + opts.pk.name]
        if ordering[0].startswith('-'):
            order_field, order_type = ordering[0][1:], 'desc'
        else:
            order_field, order_type = ordering[0], 'asc'
             
        if params.has_key(ORDER_VAR):
            try:
                field_name = opts.admin.list_display[int(params[ORDER_VAR])]
                try:
                    f = opts.get_field(field_name)
                except models.FieldDoesNotExist:
                    pass
                else:
                    if not isinstance(f.rel, models.ManyToOneRel) or not f.null:
                        order_field = f.name
            except (IndexError, ValueError):
                pass # Invalid ordering specified. Just use the default.
        if params.has_key(ORDER_TYPE_VAR) and params[ORDER_TYPE_VAR] in ('asc', 'desc'):
            order_type = params[ORDER_TYPE_VAR]
        return order_field, order_type

    def get_headers(self):
        for i, field_name in enumerate(self.list_display):
            try:
                f = self.opts.get_field(field_name)
                admin_order_field = None
            except models.FieldDoesNotExist:
                # For non-field list_display values, check for the function
                # attribute "short_description". If that doesn't exist, fall back
                # to the method name. And __str__ and __unicode__ are special-cases.
                if field_name == '__unicode__':
                    header = force_unicode(self.opts.verbose_name)
                elif field_name == '__str__':
                    header = smart_str(self.opts.verbose_name)
                else:
                    attr = getattr(self.model, field_name) # Let AttributeErrors propagate.
                    try:
                        header = attr.short_description
                    except AttributeError:
                        header = field_name.replace('_', ' ')

                # It is a non-field, but perhaps one that is sortable
                admin_order_field = getattr(getattr(self.model, field_name), "admin_order_field", None)
                if not admin_order_field:
                    yield {"text": header}
                    continue

                # So this _is_ a sortable non-field.  Go to the yield
                # after the else clause.
            else:
                if isinstance(f.rel, models.ManyToOneRel) and f.null:
                    yield {"text": f.verbose_name}
                    continue
                else:
                    header = f.verbose_name

            th_classes = []
            new_order_type = 'asc'
            if field_name == self.order_field or admin_order_field == self.order_field:
                th_classes.append('sorted %sending' % self.order_type.lower())
                new_order_type = {'asc': 'desc', 'desc': 'asc'}[self.order_type.lower()]

            yield {"text": header,
                   "sortable": True,
                   "url": self.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type}),
                   "class_attrib": mark_safe(th_classes and ' class="%s"' % ' '.join(th_classes) or '')}
                   
    def get_query_set1(self):
        qs = self.manager.get_query_set()
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR):
            if lookup_params.has_key(i):
                del lookup_params[i]

        for key, value in lookup_params.items():
            if not isinstance(key, str):
                # 'key' will be used as a keyword argument later, so Python
                # requires it to be a string.
                del lookup_params[key]
                lookup_params[smart_str(key)] = value
            # if key ends with __in, split parameter into separate values
            if key.endswith('__in'):
                lookup_params[key] = value.split(',')

        # Apply lookup parameters from the query string.
        try:
            qs = qs.filter(**lookup_params)
        # Naked except! Because we don't have any other way of validating "params".
        # They might be invalid if the keyword arguments are incorrect, or if the
        # values are not in the correct type, so we might get FieldError, ValueError,
        # ValicationError, or ? from a custom field that raises yet something else 
        # when handed impossible data.
        except:
            raise IncorrectLookupParameters

        # Use select_related() if one of the list_display options is a field
        # with a relationship.
        for field_name in self.opts.admin.list_display:
            try:
                f = self.opts.get_field(field_name)
            except models.FieldDoesNotExist:
                pass
            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    qs = qs.select_related()
                    break

        # Calculate lookup_order_field.
        # If the order-by field is a field with a relationship, order by the
        # value in the related table.
        lookup_order_field = self.order_field
        try:
            f = self.opts.get_field(self.order_field, many_to_many=False)
        except models.FieldDoesNotExist:
            pass
        else:
            if isinstance(f.rel, models.OneToOneRel):
                # For OneToOneFields, don't try to order by the related object's ordering criteria.
                pass
            elif isinstance(f.rel, models.ManyToOneRel):
                rel_ordering = f.rel.to._meta.ordering and f.rel.to._meta.ordering[0] or f.rel.to._meta.pk.column
                lookup_order_field = '%s.%s' % (f.rel.to._meta.db_table, rel_ordering)

        # Set ordering.
        qs = qs.order_by((self.order_type == 'desc' and '-' or '') + lookup_order_field)

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.opts.admin.search_fields and self.query:
            for bit in self.query.split():
                or_queries = [models.Q(**{construct_search(field_name): bit}) for field_name in self.opts.admin.search_fields]
                other_qs = QuerySet(self.model)
                if qs.select_related:
                    other_qs = other_qs.select_related()
                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                qs = qs & other_qs

        if self.opts.one_to_one_field:
            qs = qs.complex_filter(self.opts.one_to_one_field.rel.limit_choices_to)

        return qs


def list_objects(request, manager, template='objlist/object_list.html', link=True, can_add=True):
    ol = ObjectLister(request, manager)
    return render_to_response(template, {'ol': ol, 'link': link, 'can_add': can_add},
        context_instance=RequestContext(request)
    )

