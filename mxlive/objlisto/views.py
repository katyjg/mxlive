from django.contrib import admin
from django.contrib.admin.views import main
from django.core.paginator import QuerySetPaginator, InvalidPage
from django.db import models
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.encoding import force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext
from django.utils.encoding import force_text
from django.contrib.admin.options import IncorrectLookupParameters

from lims.admin import staff_site


class ObjectList(main.ChangeList):
    def __init__(self, request, manager, admin_site=None, num_show=None):
        # initialize variables
        if admin_site:
            _model_admin = admin_site._registry[manager.model]
        elif request.user.is_superuser:
            # use the staff AdminSite if available
            _model_admin = staff_site._registry.get(manager.model, admin.site._registry[manager.model])
        else:
            _model_admin = admin.site._registry[manager.model]

        self.model = manager.model
        self.model_admin = _model_admin
        self.object_type = manager.model.__name__
        self.opts = self.model._meta
        self.lookup_opts = self.opts
        self.root_queryset = manager.get_queryset()
        self.list_display = self.model_admin.list_display
        self.list_display_links = self.model_admin.list_display_links
        self.list_filter = self.model_admin.list_filter
        self.date_hierarchy = self.model_admin.date_hierarchy
        self.search_fields = self.model_admin.search_fields
        self.list_select_related = self.model_admin.list_select_related
        self.list_per_page = num_show and num_show or self.model_admin.list_per_page
        self.list_max_show_all = self.model_admin.list_max_show_all
        self.model_admin = _model_admin
        self.preserved_filters = self.model_admin.get_preserved_filters(request)

        self.unsortable = getattr(_model_admin, 'unsortable', ())
        # remove action_checkbox from list_display
        if 'action_checkbox' in self.list_display:
            self.list_display.remove('action_checkbox')
        self.manager = manager

        # Get search parameters from the query string.
        try:
            self.page_num = int(request.GET.get(main.PAGE_VAR, 1))
        except ValueError:
            self.page_num = 1
        self.show_all = main.ALL_VAR in request.GET
        self.is_popup = False
        self.to_field = request.GET.get(main.TO_FIELD_VAR)
        self.params = dict(request.GET.items())
        if main.PAGE_VAR in self.params:
            del self.params[main.PAGE_VAR]
        if main.ERROR_FLAG in self.params:
            del self.params[main.ERROR_FLAG]
        if main.TO_FIELD_VAR in self.params:
            del self.params[main.TO_FIELD_VAR]
        if main.ALL_VAR in self.params:
            del self.params[main.ALL_VAR]

        if self.is_popup:
            self.list_editable = ()
        else:
            self.list_editable = self.model_admin.list_editable

        self.query = request.GET.get(main.SEARCH_VAR, '')
        self.queryset = self.get_queryset(request)
        self.get_results(request)
        if self.is_popup:
            title = ugettext('Select %s')
        else:
            title = ugettext('Select %s to change')
        self.title = title % force_text(self.opts.verbose_name)
        self.pk_attname = self.lookup_opts.pk.attname

    def get_results(self, request):
        paginator = self.model_admin.get_paginator(request, self.queryset, self.list_per_page)
        # Get the number of objects, with admin filters applied.
        result_count = paginator.count

        # Get the total number of objects, with no admin filters applied.
        # Perform a slight optimization:
        # full_result_count is equal to paginator.count if no filters
        # were applied
        if self.get_filters_params():
            full_result_count = self.root_queryset.count()
        else:
            full_result_count = result_count
        can_show_all = result_count <= self.list_max_show_all

        # Get the list of objects to display on this page.
        try:
            self.page_obj = paginator.page(self.page_num)
        except InvalidPage:
            self.multi_page = False
            self.page_obj = None
            result_list = []
        else:
            self.multi_page = True
            result_list = self.page_obj.object_list

        self.result_count = result_count
        self.full_result_count = full_result_count
        self.object_list = result_list
        self.can_show_all = can_show_all
        self.paginator = paginator
        self.header_list = list(self.get_headers())
        self.all_shown = self.manager.count() == self.paginator.count

    def get_headers(self):

        for i, field_name in enumerate(self.model_admin.list_display):
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
                    attr = getattr(self.model, field_name)  # Let AttributeErrors propagate.
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

            if field_name == admin_order_field:
                th_classes.append('sorted %sending' % self.order_type.lower())
                new_order_type = {'asc': 'desc', 'desc': 'asc'}[self.order_type.lower()]

            yield {"text": header,
                   "sortable": not (field_name in self.unsortable),
                   "url": self.get_query_string({main.ORDER_VAR: i, main.ORDER_TYPE_VAR: new_order_type}),
                   "class_attrib": mark_safe(th_classes and ' class="%s"' % ' '.join(th_classes) or '')}


def list_objects(request, manager, template='objlist/object_list.html', link=True, can_add=True):
    """A generic view to display a list of objects retrieved through the Manager
    ``manager`` using the Template ``template``

    Keyworded options:
        - ``link`` (boolean) specifies whether or not to link each item to it's detailed page.
        - ``can_add`` (boolean) specifies whether or not new entries can be added on the list page.
    """
    ol = ObjectList(request, manager)
    return render_to_response(template, {'ol': ol, 'link': link, 'can_add': can_add, 'handler': request.path},
                              context_instance=RequestContext(request)
                              )

