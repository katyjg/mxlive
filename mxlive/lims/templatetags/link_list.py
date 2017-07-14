
from django.template import Library

from staff.models import Link

register = Library()

@register.inclusion_tag('users/help_section.html', takes_context=True)
def link_list(context):
    return { 'object': None,
            'news_links': Link.objects.filter(category=0)[:10],
            'doc_links': Link.objects.filter(category=1).order_by('frame_type','description')[:10]
            }
