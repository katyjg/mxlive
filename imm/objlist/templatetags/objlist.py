from django.template import Library
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateformat
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import get_date_formats
from django.contrib import admin
from django.conf import settings 
from django.utils.safestring import mark_safe
from django.utils.datastructures import MultiValueDict

register = Library()

@register.inclusion_tag('objlist/one_filter.html')
def show_one_filter(ol, spec):
    """
    Renders a single Filter specification ``spec`` for a given object list ``ol``. 
    """
    return {'title': spec.title(), 'choices' : list(spec.choices(ol))}

@register.inclusion_tag('objlist/filters.html')
def show_all_filters(ol):
    """
    Renders a full filter list a given object list ``ol``. 
    """
    return {'ol': ol}

@register.filter
def truncate(value, arg):
    """
    Truncates a string ``value`` after a given number of chars ``arg``.
    
    Usage::
    
        {% truncate [varname] 10 %}
    
    """
    try:
        length = int(arg)
    except ValueError: # invalid literal for int()
        return value # Fail silently.
    if not isinstance(value, basestring):
        value = str(value)
    if (len(value) > length):
        return value[:length] + "..."
    else:
        return value
        
@register.inclusion_tag('objlist/list_entry.html', takes_context=True)
def list_entry(context, obj):
    """Renders an entry for the object ``obj`` in an object list table. If the
    ``context`` contains a ``link=True`` variable, a link will be added to
    the object's detailed page.
    """ 
    ol = context.get('ol', None)
    if ol:
        model_admin = ol.model_admin
        
    checked, form = False, context.get('form', None)
    if form and hasattr(obj, 'get_form_field'):
        form_data = MultiValueDict(form.data)
        checked = str(obj.pk) in form_data.getlist(obj.get_form_field())
        
    return {'fields': list(object_fields(obj, model_admin=model_admin)),
             'object': obj,
             'link': context.get('link', False),
             'form': form,
             'checked': checked,
             'can_prioritize': context.get('can_prioritize', False),
             'request': context,
            }
       
def object_fields(obj, model_admin=None):
    model_admin = model_admin
    if not model_admin:
        model_admin = admin.site._registry[obj._default_manager.model]
    for field_name in model_admin.list_display:
        try:
            f = obj._meta.get_field(field_name)
        except models.FieldDoesNotExist:
            # For non-field list_display values, the value is either a method
            # or a property.
            try:
                attr = getattr(obj, field_name)
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                if callable(attr):
                    attr = attr()
                if boolean:
                    allow_tags = True
                    result_repr = _boolean_icon(attr)
                else:
                    result_repr = str(attr)
            except (AttributeError, ObjectDoesNotExist):
                result_repr = ''
            else:
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if not allow_tags:
                    result_repr = escape(result_repr)
        else:
            field_val = getattr(obj, f.attname)

            if isinstance(f.rel, models.ManyToOneRel):
                if field_val is not None:
                    result_repr = escape(getattr(obj, f.name))
                else:
                    result_repr = ''
            # Dates and times are special: They're formatted in a certain way.
            elif isinstance(f, models.DateField) or isinstance(f, models.TimeField):
                if field_val:
                    (date_format, datetime_format, time_format) = get_date_formats()
                    if isinstance(f, models.DateTimeField):
                        result_repr = capfirst(dateformat.format(field_val, datetime_format))
                    elif isinstance(f, models.TimeField):
                        result_repr = capfirst(dateformat.time_format(field_val, time_format))
                    else:
                        result_repr = capfirst(dateformat.format(field_val, date_format))
                else:
                    result_repr = ''
            # Booleans are special: We use images.
            elif isinstance(f, models.BooleanField) or isinstance(f, models.NullBooleanField):
                result_repr = _boolean_icon(field_val)
            # DecimalFields are special: Zero-pad the decimals.
            elif isinstance(f, models.DecimalField):
                if field_val is not None:
                    result_repr = ('%%.%sf' % f.decimal_places) % field_val
                else:
                    result_repr = ''
            # Fields with choices are special: Use the representation
            # of the choice.
            elif f.choices:
                result_repr = dict(f.choices).get(field_val, '')
            else:
                result_repr = escape(str(field_val))
        yield result_repr

def _boolean_icon(field_val):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" />' % (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[field_val], field_val)) 