from django.template import Library
from mxlive.lims.models import Container

register = Library()

@register.inclusion_tag('users/entries/dewar_table.html', takes_context=True)
def dewar_table(context, dewar, admin, page):
    containers = Container.objects.filter(dewar__exact=dewar.pk)
    return { 'containers': containers,
              'dewar': dewar,
              'admin': admin,
              'page': page
            }