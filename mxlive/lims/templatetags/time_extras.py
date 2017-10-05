from django import template
from django.utils import timezone
from datetime import datetime, timedelta


register = template.Library()


@register.simple_tag
def save_time(t):
    return t

@register.filter
def check_time(modified, last):
    if not last:
        return True
    return modified > (last + timedelta(minutes=15))
