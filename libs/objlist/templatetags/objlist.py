from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import smart_str
from django.utils.html import mark_safe, escape
from django.utils import timezone
register = template.Library()


@register.inclusion_tag('objlist/row.html', takes_context=True)
def show_row(context, obj):
    context['fields'] = get_object_fields(context, obj, context['view'])
    context['row_attrs'] = context['view'].get_row_attrs(obj)
    return context


@register.inclusion_tag('objlist/filters.html', takes_context=True)
def objlist_filters(context):
    return context


@register.simple_tag(takes_context=True)
def objlist_heading(context):
    view = context['view']
    return view.get_list_title()


@register.inclusion_tag('objlist/list.html', takes_context=True)
def objlist_list(context):
    return context


@register.inclusion_tag('objlist/tools.html', takes_context=True)
def objlist_tools(context):
    return context


@register.simple_tag(takes_context=True)
def show_grid_cell(context, obj):
    c = {'object':  obj}
    t = template.loader.get_template(context['view'].get_grid_template(obj))
    return mark_safe(t.render(c, context['request']))


def get_object_fields(context, obj, view):
    if not view.list_display:
        yield {'data': obj, 'style': ''}

    for field_name in view.list_display:
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
                if field_name in view.list_transforms:
                    result_repr = mark_safe(view.list_transforms[field_name](attr, obj))
                else:
                    result_repr = smart_str(attr)
            except (AttributeError, ObjectDoesNotExist):
                result_repr = ''
            else:
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if not allow_tags:
                    result_repr = escape(result_repr)
        else:
            field_val = getattr(obj, f.attname)
            if field_name in view.list_transforms:
                result_repr = mark_safe(view.list_transforms[field_name](field_val, obj))
            elif isinstance(f.rel, models.ManyToOneRel):
                if field_val is not None:
                    try:
                        result_repr = escape(getattr(obj, f.name))
                    except (AttributeError, ObjectDoesNotExist):
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
                m_name = 'get_{0}_display'.format(field_name)
                result_repr = getattr(obj, m_name)()
            else:
                result_repr = escape(smart_str(field_val))

        yield {'data': result_repr, 'style': view.list_styles.get(field_name, '')}


def _boolean_icon(field_val):
    if field_val:
        return mark_safe('<i class="fa fa-check-circle"></i>')
    else:
        return ''
