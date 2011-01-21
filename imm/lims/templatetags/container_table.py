from django import template
from django.template import Library

register = Library()

@register.inclusion_tag('lims/entries/container_table.html', takes_context=True)
def container_table(context, object, admin):
    return { 'object': object,
            'admin': admin
            }
