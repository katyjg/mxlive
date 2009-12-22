# Create your views here.
from django.core.paginator import QuerySetPaginator, InvalidPage
from django.utils.encoding import force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.db import models
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.template import RequestContext
from django.shortcuts import render_to_response

MAX_SHOW_ALL_ALLOWED = 200
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
ERROR_FLAG = 'e'
IS_POPUP_VAR = 'pop'
TO_FIELD_VAR = 't'
   
    

class ObjectList(ChangeList):
    """ A Clone of the Admin ChangeList which enables us to use changelist like
    features such as filters, search and pagination in non-admin related applications
    """
    
    def __init__(self, request, manager):
        self.manager = manager
        self.model = self.manager.model
        self.object_type = self.model.__name__
        self.opts = self.model._meta
        self.lookup_opts = self.opts
        
        # initialize variables
        self.model_admin = admin.site._registry[self.model]
        self.root_query_set = self.manager.get_query_set()
        self.list_display = self.model_admin.list_display
        self.list_display_links = self.model_admin.list_display_links
        self.list_filter = self.model_admin.list_filter
        self.date_hierarchy = self.model_admin.date_hierarchy
        self.search_fields = self.model_admin.search_fields
        self.list_select_related = self.model_admin.list_select_related
        self.list_per_page = self.model_admin.list_per_page
        self.list_editable = []
        
        # remove action_checkbox from list_display
        if 'action_checkbox' in self.list_display:
            self.list_display.remove('action_checkbox')
            
        # Get search parameters from the query string.
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 1))
        except ValueError:
            self.page_num = 1
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
        self.total_count = self.manager.count()   
        self.all_shown = paginator.count == self.total_count
        self.header_list = list(self.get_headers())
        try:
            self.page_obj = paginator.page(self.page_num)
        except InvalidPage:
            self.is_paginated = False
            self.page_obj = None
            self.object_list = self.query_set.all()
        else:
            self.is_paginated = True
            self.object_list = self.page_obj.object_list
        self.paginator = paginator
        self.result_count = self.paginator.count
        
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
                    print field_name
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
                   

def list_objects(request, manager, template='objlist/object_list.html', link=True, can_add=True):
    """A generic view to display a list of objects retrieved through the Manager
    ``manager`` using the Template ``template``
    
    Keyworded options:
        - ``link`` (boolean) specifies whether or not to link each item to it's detailed page.
        - ``can_add`` (boolean) specifies whether or not new entries can be added on the list page.   
    """ 
    ol = ObjectList(request, manager)
    return render_to_response(template, {'ol': ol, 'link': link, 'can_add': can_add},
        context_instance=RequestContext(request)
    )

