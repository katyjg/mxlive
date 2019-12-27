from django import template
from django.utils.safestring import mark_safe
import json

register = template.Library()


@register.filter
def to_json(data):
    return mark_safe(json.dumps(data))


@register.filter
def from_json(data):
    return json.loads(data)
