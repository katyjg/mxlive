from django.template import Library

from mxlive.staff import models

register = Library()

@register.inclusion_tag('users/announcements.html', takes_context=True)
def load_announcements(context):
    return {'announcements': models.Announcement.objects.all(),
            'request': context}