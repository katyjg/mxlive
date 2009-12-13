from django.template import Library
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import dateformat
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import get_date_formats, get_partial_date_formats
from django.contrib import admin

register = Library()

@register.inclusion_tag('objlist/one_filter.html')
def filter(ol, spec):
    return {'title': spec.title(), 'choices' : list(spec.choices(ol))}

@register.inclusion_tag('objlist/filters.html')
def filters(ol):
    return {'ol': ol}

@register.filter
def truncate(value, arg):
    """
    Truncates a string after a given number of chars  
    Argument: Number of chars to truncate after
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
    return {'fields': list(object_fields(obj)),
             'object': obj,
             'link': context['link'],
            }
       
def object_fields(obj):
    first = True
    pk = obj._meta.pk.attname
    model_admin = admin.site._registry[obj._default_manager.model]
    for field_name in model_admin.list_display:
        row_class = ''
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
                row_class = ' class="nowrap"'
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

