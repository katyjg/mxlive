
from django.template import Library

register = Library()

@register.simple_tag
def get_location(automounter, container):
    ret_val = automounter.get_position(container)
    return ret_val

