
from django.template import Library

from staff.models import Announcement

register = Library()


@register.inclusion_tag('users/announcements.html', takes_context=True)
def load_announcements(context):
    context['announcements'] = Announcement.objects.all()
    return context
