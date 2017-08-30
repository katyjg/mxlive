from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
def json_to_dict(data):
    return mark_safe(json.dumps(data))