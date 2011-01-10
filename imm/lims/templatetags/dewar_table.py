from django import template
from django.template import Library
from lims.models import Container

register = Library()

@register.inclusion_tag('lims/entries/dewar_table.html', takes_context=True)
def dewar_table(context, dewar, admin):
    containers = Container.objects.filter(dewar__exact=dewar.pk)
    return { 'containers': containers,
              'dewar': dewar,
              'admin': admin
            }
