from django import template
from django.template import Library

from imm.staff.models import Link

register = Library()

@register.inclusion_tag('lims/help_section.html', takes_context=True)
def link_list(context):
    return { 'object': object,
            'news_links': Link.objects.filter(category=0)[:10],
            'doc_links': Link.objects.filter(category=1)[:10]
            }
