from django import template
from django.template import Library

from imm.staff.models import Link

register = Library()

@register.inclusion_tag('lims/help_section.html', takes_context=True)
def link_list(context):
    links = Link.objects.filter(category=0)[:5]
    for link in Link.objects.filter(category=1)[:5]:
        links.append(link)
    return { 'object': object,
            'links': links
            }
